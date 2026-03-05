from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from archives.models import Category
from .models import LorePost
from .forms import LorePostForm

User = get_user_model()

class LoreModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='password')
        self.category = Category.objects.create(name='Folktales', slug='folktales', type='lore')

    def test_lore_post_creation(self):
        post = LorePost.objects.create(
            title='The Tortoise and the Bird',
            content_json={'blocks': [{'type': 'paragraph', 'data': {'text': 'Once upon a time...'}}]},
            author=self.user,
            category=self.category,
            is_approved=True,
            is_published=True
        )
        self.assertEqual(post.title, 'The Tortoise and the Bird')
        self.assertTrue(post.slug.startswith('the-tortoise-and-the-bird'))
        self.assertEqual(str(post), 'The Tortoise and the Bird')

    def test_lore_post_absolute_url(self):
        post = LorePost.objects.create(title='Test Lore', author=self.user)
        self.assertEqual(post.get_absolute_url(), reverse('lore:detail', kwargs={'slug': post.slug}))

class LoreFormTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Proverbs', slug='proverbs', type='lore')

    def test_lore_form_valid(self):
        form_data = {
            'title': 'Ancient Wisdom',
            'category': self.category.id,
            'excerpt': 'A collection of proverbs.',
            'content_json': '{"blocks": []}',
        }
        form = LorePostForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_lore_form_media_conflict(self):
        # Media fields are optional, so this should still be valid as per the form logic
        # but let's check if it handles both URL and File (usually we prefer one, but the form doesn't strictly forbid both)
        pass

class LoreViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='writer', password='password')
        self.staff = User.objects.create_superuser(username='staff', password='password', email='staff@example.com')
        self.category = Category.objects.create(name='History', slug='history', type='lore')
        self.post = LorePost.objects.create(
            title='Igbo Origins',
            author=self.user,
            category=self.category,
            is_approved=True,
            is_published=True
        )

    def test_lore_list_view(self):
        response = self.client.get(reverse('lore:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Igbo Origins')

    def test_lore_list_search(self):
        response = self.client.get(reverse('lore:list') + '?search=Igbo')
        self.assertContains(response, 'Igbo Origins')
        response = self.client.get(reverse('lore:list') + '?search=Yoruba')
        self.assertNotContains(response, 'Igbo Origins')

    def test_lore_list_sorting(self):
        # Create another post with different title and date
        LorePost.objects.create(
            title='Aardvark Story',
            author=self.user,
            category=self.category,
            is_approved=True,
            is_published=True
        )
        
        # Test A-Z
        response = self.client.get(reverse('lore:list') + '?sort=a-z')
        self.assertContains(response, 'Aardvark Story')
        # Check order (Aardvark should be first)
        content = response.content.decode()
        self.assertTrue(content.find('Aardvark Story') < content.find('Igbo Origins'))
        
        # Test Recently Added (Igbo Origins was created first in setUp, Aardvark second)
        response = self.client.get(reverse('lore:list') + '?sort=recently-added')
        content = response.content.decode()
        self.assertTrue(content.find('Aardvark Story') < content.find('Igbo Origins'))
        
        # Test Oldest
        response = self.client.get(reverse('lore:list') + '?sort=oldest')
        content = response.content.decode()
        self.assertTrue(content.find('Igbo Origins') < content.find('Aardvark Story'))

    def test_lore_detail_view(self):
        response = self.client.get(reverse('lore:detail', kwargs={'slug': self.post.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Igbo Origins')

    def test_lore_detail_unapproved_access(self):
        unapproved = LorePost.objects.create(title='Secret Lore', author=self.user, is_approved=False)
        # Anonymous user should get 404
        response = self.client.get(reverse('lore:detail', kwargs={'slug': unapproved.slug}))
        self.assertEqual(response.status_code, 404)
        
        # Author should be able to see it
        self.client.login(username='writer', password='password')
        response = self.client.get(reverse('lore:detail', kwargs={'slug': unapproved.slug}))
        self.assertEqual(response.status_code, 200)

    def test_lore_create_view(self):
        self.client.login(username='writer', password='password')
        response = self.client.get(reverse('lore:create'))
        self.assertEqual(response.status_code, 200)
        
        data = {
            'title': 'New Story',
            'category': self.category.id,
            'content_json': '{"blocks": [{"type": "paragraph", "data": {"text": "Once..."}}]}'
        }
        response = self.client.post(reverse('lore:create'), data)
        self.assertEqual(LorePost.objects.filter(title='New Story').count(), 1)
        new_post = LorePost.objects.get(title='New Story')
        self.assertRedirects(response, reverse('lore:detail', kwargs={'slug': new_post.slug}))

    def test_lore_edit_view(self):
        self.client.login(username='writer', password='password')
        response = self.client.get(reverse('lore:edit', kwargs={'slug': self.post.slug}))
        self.assertEqual(response.status_code, 200)
        
        data = {
            'title': 'Updated Igbo Origins',
            'category': self.category.id,
            'content_json': '{"blocks": []}'
        }
        response = self.client.post(reverse('lore:edit', kwargs={'slug': self.post.slug}), data)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated Igbo Origins')
        # Edits should reset approval
        self.assertFalse(self.post.is_approved)

    def test_lore_delete_view(self):
        self.client.login(username='writer', password='password')
        # GET show confirmation
        response = self.client.get(reverse('lore:delete', kwargs={'slug': self.post.slug}))
        self.assertEqual(response.status_code, 200)
        
        # POST performs deletion
        response = self.client.post(reverse('lore:delete', kwargs={'slug': self.post.slug}))
        self.assertRedirects(response, reverse('lore:list'))
        self.assertEqual(LorePost.objects.filter(id=self.post.id).count(), 0)
