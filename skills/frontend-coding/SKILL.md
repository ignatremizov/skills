---
name: frontend-coding
description: Use for frontend coding and review tasks involving UI implementation, visual design, layout, interaction design, responsive behavior, accessibility, frontend polish, web app surfaces, landing pages, games, dashboards, or other user-facing interface work.
---

# Frontend Coding

Use this skill when building or reviewing a frontend experience.

## Build With Empathy

- Match the existing product, framework, and design system when one exists.
- Think deeply about the audience and use case before choosing layout, components, visual style, on-screen text, and interaction patterns.
- Tailor the visual language to the domain. SaaS, CRM, compliance, finance, admin, and operational tools should feel quiet, utilitarian, scan-friendly, and efficient rather than decorative or marketing-heavy.
- Games, creative tools, portfolios, and editorial surfaces can be more expressive, animated, illustrative, and playful.
- Build common workflows so users can move naturally between views without dead ends or placeholder-only states.
- Start with the primary workflow or screen users need most.
- Use real product vocabulary and data where available. When data is illustrative, make it clearly sample data rather than implied production state.

## Interface Choices

- Use icons for common tool buttons, swatches for color, segmented controls for modes, toggles or checkboxes for binary settings, sliders/steppers/inputs for numeric values, menus for option sets, and tabs for views.
- Prefer familiar symbols over rounded text buttons when the command has a standard icon, such as undo, redo, bold, italic, save, download, or zoom.
- Use familiar icon libraries already present in the app; prefer lucide icons when available.
- Add tooltips for unfamiliar icon-only controls.
- Build expected controls, states, and views for the target workflow.
- Include relevant loading, empty, error, disabled, hover, focus, and active states.
- Use semantic structure, visible focus, keyboard paths, sufficient contrast, and reduced-motion support where they apply.
- Keep visible app copy focused on user goals, state, and next actions. Add instructional text only when the product genuinely needs it.
- Use layout primitives intentionally: full-width sections, grids, lists, tables, panels, modals, and framed item groups each have a place. Follow the existing design system.

## Visual Direction

- Choose a clear visual direction and palette that fit the domain and existing design system.
- Let hierarchy come from clear structure, spacing, alignment, typography, and purposeful surface boundaries.
- Choose a palette with a clear primary role, supportive neutrals, and limited accents; check the finished screen for balanced contrast and mood across the full viewport.
- Build background atmosphere with purposeful layout, media, texture, structure, or surfaces where appropriate.
- Use atmosphere that comes from product-relevant material, such as real media, data, maps, diagrams, texture, motion, or interaction.
- If the user requests decorative abstraction, make it support the product rather than dominate the screen.
- For greenfield UI, choose one domain-specific signature move and keep the surrounding interface disciplined.
- Reserve hero-scale type for true heroes; dense product surfaces need tighter, scannable headings.
- Use stable type sizes. Keep letter spacing at 0 unless the existing system requires otherwise.

## Landing And Hero Pages

- For landing-page heroes, prefer a relevant image, generated bitmap image, or immersive full-bleed interactive scene as the background with text over it.
- On branded, product, venue, portfolio, or object-focused pages, make the brand/product/place/object visible in the first viewport, not only in tiny nav text.
- Hero content should leave a hint of the next section visible on mobile and desktop, including wide desktop.
- Make the H1 the brand, product, place, person, literal offer, or category; put descriptive value props in supporting copy.

## Layout And Responsiveness

- Ensure desktop and mobile layouts both load correctly.
- Give each layout primitive a specific job: page regions organize the screen, panels group related work, and repeated items stay compact and easy to scan.
- Define stable dimensions for boards, grids, toolbars, icon buttons, counters, tiles, and other fixed-format controls.
- Ensure text fits its parent at all supported viewport sizes.
- Move text to a new line when needed; if it still does not fit, use dynamic sizing so the longest word fits.
- Text should not occlude preceding or following content.
- Prevent hover states, labels, icons, loading text, and dynamic content from shifting layout.
- Verify that UI elements and text do not overlap.
- Match display text size to its container; dense surfaces need compact, scannable type.
- Use type scales tied to content density and component purpose; adjust at intentional breakpoints so headings, controls, and data remain proportional.

## Media And 3D

- Websites and games should use meaningful visual assets when visuals are part of the task.
- Use real or generated bitmap images when the user needs to inspect a product, place, object, person, state, gameplay, or concrete output.
- Use clear, inspectable media when the user needs to inspect the real subject.
- Use custom SVG, canvas, Three.js, or game-native assets for specific game assets when that is a better fit than bitmap media.
- For games or interactive tools with established rules, physics, parsing, or engines, use proven libraries for core domain logic unless the user asks for a from-scratch implementation.
- For primary 3D experiences, use Three.js and let the scene own the available space rather than burying it in generic chrome.
- For primary 3D, canvas, or asset-heavy work, verify the rendered view contains meaningful content, occupies the intended frame, responds to input or time as designed, and keeps surrounding UI readable on desktop and mobile.
- Confirm referenced assets, textures, and media appear in the rendered experience, especially when the user needs to inspect a real object, state, product, place, or gameplay moment.

## Runtime Verification

- When a site or app needs a dev server, start it after implementation and provide the URL.
- If the intended output works as static HTML, provide the local file path instead of starting a server.
- If a requested port is occupied, use another port.
- For nontrivial visual changes, inspect the rendered UI with a browser screenshot or equivalent visual check when feasible.
