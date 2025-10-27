# Igbo Archives Platform

**Preserving the Past, Inspiring the Future**

A comprehensive Django-based web platform for preserving and celebrating Igbo culture, history, and heritage. This platform features a heritage-inspired design with sepia tones and vintage aesthetics, modern content management, and comprehensive community engagement tools.

## 🌟 Overview

Igbo Archives is a dedicated platform for preserving and celebrating the history and culture of the Igbo people. Built with Django 4.2, the platform offers a museum-quality experience for browsing cultural archives, community insights, and book reviews.

## ✨ Key Features

### Core Functionality
- **Cultural Archives**: Curated collection of Igbo artifacts, photographs, documents, and historical materials with comprehensive metadata
- **Insights**: Community-generated articles using Quill rich text editor with image management
- **Book Reviews**: Reviews and discussions of literature related to Igbo history and culture
- **AI Chat Assistant**: External link to Igbo Archives AI for exploring Igbo heritage
- **Academy**: Educational landing page with information about Igbo language and traditions

### Content Features
- **Random Archives Carousel**: Homepage carousel showcasing approved archives in randomized order
- **A-Z/Z-A Sorting**: Alphabetical sorting options for easy archive browsing
- **Responsive Filtering**: HTMX-powered dynamic filtering by category, type, and search
- **Grid/List Views**: Toggle between grid and list views with persistent user preferences
- **Archive Media Browser**: Select images from existing archives when creating posts
- **Image Upload with Metadata**: Required caption and description for all uploaded images
- **Auto-Archive Creation**: Uploaded images automatically create archive entries pending admin approval

### User Experience
- **Heritage-Inspired Design**: Sepia tones, vintage colors, and aged paper aesthetics
- **Sticky Shrinking Header**: Header reduces to 1/3 size on scroll for more content space
- **4-Column Footer**: Responsive footer with Quick Links, Resources, and Community sections
- **Profile Dropdown**: Quick access to profile, dashboard, messages, and notifications
- **Notification System**: Bell icon with dropdown showing unread notifications
- **Dark Mode**: User-toggleable dark/light theme with logo switching

### Technical Features
- **Progressive Web App (PWA)**: Installable on mobile and desktop devices
- **Email-Based Authentication**: Secure signup/login using django-allauth
- **Social Authentication**: Google OAuth integration
- **Push Notifications**: Web push notifications for user engagement
- **Threaded Comments**: Rich discussions with guest participation (reCAPTCHA protected)
- **Quill Editor**: Modern rich text editor with enhanced image upload button
- **Dynamic Filtering**: HTMX-powered content filtering without page reloads
- **SEO Optimized**: Meta tags, Open Graph, and XML sitemaps
- **Responsive Design**: Mobile-first design optimized for all screen sizes

## 📋 Project Structure

```
igbo-archives-platform/
├── academy/                    # Academy app
├── api/                        # API endpoints (image upload, archive browser)
├── archives/                   # Cultural Archives app
│   ├── migrations/
│   │   └── 0003_remove_is_featured_field.py  # Removed featured functionality
│   ├── templates/archives/
│   ├── admin.py               # Admin with inline editing for category & approval
│   ├── models.py              # Archive model (no is_featured field)
│   └── views.py               # Random carousel, A-Z/Z-A sorting
├── books/                      # Book Reviews app
├── core/                       # Core app with base templates
│   ├── static/
│   │   ├── css/style.css      # Heritage design system, 4-column footer
│   │   └── js/main.js         # Profile dropdown, notifications, carousels
│   ├── templates/
│   │   ├── base.html          # Updated header, footer, navigation
│   │   ├── core/home.html     # Homepage with random carousel
│   │   └── partials/recommended_carousel.html
│   └── views.py               # Random archives for homepage
├── insights/                   # User Insights app
│   ├── templates/insights/
│   │   └── create.html        # Enhanced Quill editor with obvious image button
│   └── models.py
├── users/                      # User management app
├── media/                      # User-uploaded media files
├── static/images/logos/        # Logo files (dark and light versions)
├── db.sqlite3                  # SQLite database
├── manage.py
├── plan.md                     # Development roadmap
├── README.md                   # This file
└── requirements.txt
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- pip (Python package installer)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd igbo-archives-platform
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   # Django Settings
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   
   # Google OAuth (optional)
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   
   # reCAPTCHA (optional)
   RECAPTCHA_PUBLIC_KEY=your-recaptcha-site-key
   RECAPTCHA_PRIVATE_KEY=your-recaptcha-secret-key
   
   # Firebase Cloud Messaging (for push notifications)
   VAPID_PUBLIC_KEY=your-vapid-public-key
   VAPID_PRIVATE_KEY=your-vapid-private-key
   
   # Email Settings
   DEFAULT_FROM_EMAIL=noreply@igboarchives.com
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Collect static files**
   ```bash
   python manage.py collectstatic --noinput
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver 0.0.0.0:5000
   ```

8. **Access the application**
   - Open your browser and navigate to `http://localhost:5000`
   - Admin panel: `http://localhost:5000/admin`

## 🎨 Design System

### Color Palette
The platform uses a heritage-inspired color scheme:
- **Sepia Tones**: Reminiscent of aged photographs
- **Vintage Gold**: Accent color for CTAs and highlights
- **Desert Sand**: Warm, earthy secondary colors
- **Aged Paper**: Background tones that evoke historical documents

### Typography
- **Headings**: Playfair Display (serif, elegant)
- **Body**: Inter (sans-serif, readable)

## 📝 Key Models

### Archive (archives/models.py)
- Stores cultural artifacts with comprehensive metadata
- **Removed**: `is_featured` field (completely removed from database)
- **Fields**: title, description, caption, alt_text, archive_type, image, category, tags
- **Admin**: Inline editing for category and is_approved status
- **Validation**: File size limits, required metadata

### InsightPost (insights/models.py)
- User-generated articles with Quill editor content
- **Image handling**: Uploaded images create archive entries (pending approval)
- **Title from caption**: Archive title uses image caption, not filename
- **Fields**: title, content, excerpt, featured_image, author, is_published, is_approved

### CustomUser (users/models.py)
- Extended user model with full_name (displayed throughout site)
- **Profile features**: Bio, profile picture, social links
- **Display**: full_name used everywhere, username only in URLs

## 🛠️ Management Commands

### Backup Database
```bash
python manage.py backup_database
```

### Delete Old Drafts (30+ days)
```bash
python manage.py delete_old_drafts
```

## 🔒 Security Features

- CSRF protection with trusted origins
- Password validation (minimum length, complexity)
- Secure session management
- reCAPTCHA on forms (configurable)
- SQL injection protection via Django ORM
- File upload validation (size, type)

## 📱 Mobile Features

- Responsive design with mobile-first approach
- Fixed bottom navigation on mobile
- Touch-friendly interface
- PWA installation prompt
- Sticky header that shrinks on scroll

## 🔍 SEO & Social

- XML sitemaps for all content types
- Open Graph tags for social sharing
- Twitter Card support
- robots.txt configuration

## 📦 Key Dependencies

- **Django 4.2**: Web framework
- **django-allauth**: Authentication
- **django-htmx**: Dynamic interactions
- **django-pwa**: Progressive Web App
- **Pillow**: Image processing
- **django-taggit**: Tagging system
- **django-quill-editor**: Rich text editing

## 🚢 Deployment

### Production Checklist

1. Set `DEBUG=False`
2. Update `ALLOWED_HOSTS` with your domain
3. Configure `CSRF_TRUSTED_ORIGINS`
4. Set up PostgreSQL database
5. Configure static file serving
6. Set up SSL certificate
7. Configure email backend
8. Set strong `SECRET_KEY`

### Deployment Command
```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port igbo_archives.wsgi:application
```

## 📧 Contact

For inquiries, suggestions, or contributions:
- Website: [igboarchives.com.ng](https://igboarchives.com.ng)
- Email: igboarchives@gmail.com

## 🙏 Acknowledgments

- All contributors to Igbo cultural preservation
- Museum collections providing historical photographs
- The Igbo community for their support and engagement

---

**Thank you for being a part of Igbo Archives. Together, we ensure that the history and culture of the Igbo people are preserved for future generations.**
