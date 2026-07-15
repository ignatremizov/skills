#!/usr/bin/env perl

use strict;
use warnings;

use Cwd qw(abs_path);
use File::Basename qw(dirname);
use File::Temp qw(tempfile);
use Getopt::Long qw(GetOptions);

my $in_place = 0;
my $help = 0;

GetOptions(
    'in-place|i' => \$in_place,
    'help|h'     => \$help,
) or usage(2);

usage(0) if $help;

if ($in_place && !@ARGV) {
    die "unwrap.pl: --in-place requires at least one file\n";
}

if (!$in_place && @ARGV > 1) {
    die "unwrap.pl: multiple files require --in-place\n";
}

if ($in_place) {
    unwrap_file_in_place($_) for @ARGV;
    exit 0;
}

my $input;
if (@ARGV && $ARGV[0] ne '-') {
    $input = read_file($ARGV[0]);
} else {
    local $/;
    $input = <STDIN> // q{};
}

print unwrap_markdown($input);

sub unwrap_file_in_place {
    my ($path) = @_;

    die "unwrap.pl: cannot edit standard input in place\n" if $path eq '-';

    my $target = -l $path ? abs_path($path) : $path;
    die "unwrap.pl: cannot resolve symlink '$path'\n" if !defined $target;

    my $input = read_file($target);
    my $output = unwrap_markdown($input);
    return if $output eq $input;

    my @stat = stat $target;
    die "unwrap.pl: cannot stat '$path': $!\n" if !@stat;

    my ($temp_fh, $temp_path) = tempfile(
        '.unwrap-XXXXXX',
        DIR    => dirname($target),
        UNLINK => 0,
    );

    binmode $temp_fh;
    print {$temp_fh} $output
        or die "unwrap.pl: cannot write '$temp_path': $!\n";
    close $temp_fh
        or die "unwrap.pl: cannot close '$temp_path': $!\n";

    chmod($stat[2] & 07777, $temp_path)
        or die "unwrap.pl: cannot preserve permissions for '$path': $!\n";
    rename($temp_path, $target)
        or die "unwrap.pl: cannot replace '$path': $!\n";
}

sub read_file {
    my ($path) = @_;

    open my $fh, '<', $path
        or die "unwrap.pl: cannot read '$path': $!\n";
    binmode $fh;
    local $/;
    my $content = <$fh> // q{};
    close $fh
        or die "unwrap.pl: cannot close '$path': $!\n";

    return $content;
}

sub unwrap_markdown {
    my ($content) = @_;

    my $newline = $content =~ /\r\n/ ? "\r\n" : "\n";
    my @lines = split /\r?\n/, $content, -1;
    my @output;
    my $buffer = q{};
    my $buffer_kind = q{};
    my $fence_character = q{};
    my $fence_length = 0;
    my $in_front_matter = 0;
    my $in_table = 0;

    my $flush = sub {
        if (length $buffer) {
            push @output, $buffer;
            $buffer = q{};
            $buffer_kind = q{};
        }
    };

    for my $index (0 .. $#lines) {
        my $line = $lines[$index];

        if ($index == 0 && $line eq '---') {
            $flush->();
            push @output, $line;
            $in_front_matter = 1;
            next;
        }

        if ($in_front_matter) {
            push @output, $line;
            $in_front_matter = 0 if $line eq '---' || $line eq '...';
            next;
        }

        if (length $fence_character) {
            push @output, $line;
            if ($line =~ /^\s*\Q$fence_character\E{$fence_length,}\s*$/) {
                $fence_character = q{};
                $fence_length = 0;
            }
            next;
        }

        if ($line =~ /^\s*(`{3,}|~{3,})/) {
            $flush->();
            push @output, $line;
            $fence_character = substr $1, 0, 1;
            $fence_length = length $1;
            next;
        }

        if ($line eq q{}) {
            $flush->();
            push @output, q{};
            $in_table = 0;
            next;
        }

        my $next_line = $index < $#lines ? $lines[$index + 1] : q{};
        my $starts_table =
            $line =~ /\|/
            && $next_line =~ /^\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$/;

        if ($starts_table || $in_table || $line =~ /^\s*\|/) {
            $flush->();
            push @output, $line;
            $in_table = 1;
            next;
        }

        if (
            $line =~ /^\s*(?:#{1,6})(?:\s|$)/
            || $line =~ /^\s*(?:={3,}|-{3,}|\*{3,}|_{3,})\s*$/
            || $line =~ /^\s*\[[^\]]+\]:\s+\S/
            || $line =~ /^\s*>/
            || $line =~ /^\s*</
            || (!length $buffer && $line =~ /^(?:\t| {4})/)
        ) {
            $flush->();
            push @output, $line;
            next;
        }

        if ($line =~ /^(\s*)(?:\d+[.)]|[-+*]|\xE2\x80\xA2)\s+\S/) {
            $flush->();
            $buffer = $line;
            $buffer_kind = 'list';
            next;
        }

        if (length $buffer && ($buffer =~ / {2}\z/ || $buffer =~ /\\\z/)) {
            $flush->();
        }

        if (length $buffer_kind && $buffer_kind eq 'list') {
            append_wrapped_line(\$buffer, $line);
            next;
        }

        if (length $buffer) {
            append_wrapped_line(\$buffer, $line);
        } else {
            $buffer = $line;
            $buffer_kind = 'paragraph';
        }
    }

    $flush->();

    return join $newline, @output;
}

sub append_wrapped_line {
    my ($buffer_ref, $line) = @_;

    $line =~ s/^\s+//;
    $$buffer_ref =~ s/[ \t]+\z//;

    # Preserve wrapped paths and inline expressions. Unicode arrows are matched
    # as UTF-8 bytes because file content is intentionally processed losslessly.
    my $ends_with_connector =
        $$buffer_ref =~ m{(?:[/(\[]|->|=>)\z}
        || $$buffer_ref =~ /(?:\xE2\x86\x92|\xE2\x9F\xB6|\xE2\x86\x90|\xE2\x86\x94|\xE2\x87\x92|\xE2\x9F\xB9)\z/;

    $$buffer_ref .= ($ends_with_connector ? q{} : q{ }) . $line;
}

sub usage {
    my ($exit_code) = @_;

    print <<'USAGE';
Usage:
  unwrap.pl [FILE]
  unwrap.pl < FILE
  unwrap.pl --in-place FILE [FILE ...]

Unwrap soft-wrapped Markdown prose while preserving block structure, tables,
front matter, fenced and indented code, block quotes, and explicit hard breaks.

Options:
  -i, --in-place  Replace files atomically instead of writing to stdout
  -h, --help      Show this help
USAGE

    exit $exit_code;
}
