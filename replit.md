# Igbo Archives - Django Application

## Overview
Igbo Archives is a digital platform for preserving and celebrating the history and culture of the Igbo people. It features cultural archives, community insights, book reviews, and educational resources.

## Tech Stack
- **Backend**: Django 5.2.9, Python 3.11
- **Frontend**: Tailwind CSS (migrated from Bootstrap)
- **Rich Text Editor**: Editor.js (migrated from Quill)
- **Interactivity**: HTMX for dynamic updates
- **Database**: PostgreSQL (Neon-backed)

## Recent Changes (December 2025)

### Frontend Modernization Complete
1. **Tailwind CSS Migration**
   - Replaced Bootstrap with Tailwind CSS
   - Created vintage heritage color palette (sepia tones, bronze, aged-parchment aesthetic)
   - Built reusable component classes (buttons, cards, forms, navigation)
   - All templates updated with Tailwind utility classes

2. **Editor.js Integration**
   - Replaced Quill editor with Editor.js
   - Custom image upload functionality with archive selection
   - Featured image picker integrated
   - Content conversion between formats supported

3. **External Assets**
   - All inline CSS moved to external files
   - All inline JavaScript moved to external modules
   - Modular asset structure created

4. **CDN Removal**
   - Bootstrap CDN removed (local Tailwind used)
   - All fonts served locally
   - Google Analytics externalized to analytics.js

## Project Structure
```
igbo_archives/          # Django project settings
core/                   # Core app (base templates, static files)
  ├── static/
  │   ├── css/
  │   │   ├── tailwind.input.css    # Tailwind source
  │   │   ├── tailwind.output.css   # Compiled CSS
  │   │   ├── style.css             # Custom styles
  │   │   ├── editor.css            # Editor.js styles
  │   │   └── modal.css             # Modal styles
  │   ├── js/
  │   │   ├── main.js               # Main JS
  │   │   ├── editor.js             # Editor.js wrapper
  │   │   ├── insight-editor.js     # Insight editor module
  │   │   └── analytics.js          # Analytics
  │   └── vendor/
  │       ├── css/                  # Vendor CSS (fonts, etc)
  │       └── js/
  │           └── editorjs/         # Editor.js plugins
  └── templates/
      ├── base.html                 # Main base template
      └── account/                  # Auth templates
archives/               # Cultural archives app
insights/               # Community insights app
books/                  # Book reviews app
users/                  # User profiles app
academy/                # Academy app (coming soon)
ai/                     # AI features app (coming soon)
```

## Build Commands
```bash
# Build Tailwind CSS (required after template changes)
npm run build:css

# Watch Tailwind CSS for development
npm run watch:css

# Run Django development server
python manage.py runserver 0.0.0.0:5000
```

## Color Palette (Vintage Heritage)
- Dark Brown: #3D2817 (primary text)
- Vintage Gold: #B8974F (accents, buttons)
- Vintage Bronze: #9D7A3E (hover states)
- Heritage Cream: #F0F0DA (backgrounds)
- Sepia tones for muted text and borders

## User Preferences
- No inline CSS or JavaScript
- All assets served locally (no CDN dependencies)
- Vintage/heritage aesthetic maintained throughout
- Mobile-first responsive design
- Accessibility-focused (WCAG AA)
