from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
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

    def test_submitted_at_field(self):
        """Verify submitted_at is nullable and works with moderation flow."""
        post = LorePost.objects.create(title='Draft Post', author=self.user)
        self.assertIsNone(post.submitted_at)
        
        from django.utils import timezone
        post.submitted_at = timezone.now()
        post.pending_approval = True
        post.save()
        post.refresh_from_db()
        self.assertIsNotNone(post.submitted_at)
        self.assertTrue(post.pending_approval)

class LoreFormTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Proverbs', slug='proverbs', type='lore')

    def test_lore_form_valid(self):
        form_data = {
            'title': 'Ancient Wisdom',
            'category': self.category.id,
            'excerpt': 'A collection of proverbs.',
        }
        form = LorePostForm(data=form_data)
        self.assertTrue(form.is_valid())


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
        LorePost.objects.create(
            title='Aardvark Story',
            author=self.user,
            category=self.category,
            is_approved=True,
            is_published=True
        )
        
        response = self.client.get(reverse('lore:list') + '?sort=a-z')
        self.assertContains(response, 'Aardvark Story')
        content = response.content.decode()
        self.assertTrue(content.find('Aardvark Story') < content.find('Igbo Origins'))
        
        response = self.client.get(reverse('lore:list') + '?sort=recently-added')
        content = response.content.decode()
        self.assertTrue(content.find('Aardvark Story') < content.find('Igbo Origins'))
        
        response = self.client.get(reverse('lore:list') + '?sort=oldest')
        content = response.content.decode()
        self.assertTrue(content.find('Igbo Origins') < content.find('Aardvark Story'))

    def test_lore_detail_view(self):
        response = self.client.get(reverse('lore:detail', kwargs={'slug': self.post.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Igbo Origins')

    def test_lore_detail_has_prev_next_context(self):
        """Verify the detail view provides prev/next navigation context."""
        second_post = LorePost.objects.create(
            title='Second Post', author=self.user, category=self.category,
            is_approved=True, is_published=True
        )
        response = self.client.get(reverse('lore:detail', kwargs={'slug': second_post.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('previous_post', response.context)
        self.assertIn('next_post', response.context)

    def test_lore_detail_unapproved_access(self):
        unapproved = LorePost.objects.create(title='Secret Lore', author=self.user, is_approved=False)
        response = self.client.get(reverse('lore:detail', kwargs={'slug': unapproved.slug}))
        self.assertEqual(response.status_code, 404)
        
        self.client.login(username='writer', password='password')
        response = self.client.get(reverse('lore:detail', kwargs={'slug': unapproved.slug}))
        self.assertEqual(response.status_code, 200)

    def test_lore_create_submit_workflow(self):
        """Submitting a lore post should set pending_approval=True, is_published=False."""
        self.client.login(username='writer', password='password')
        response = self.client.get(reverse('lore:create'))
        self.assertEqual(response.status_code, 200)
        
        data = {
            'title': 'New Story',
            'category': self.category.id,
            'content_json': '{"blocks": [{"type": "paragraph", "data": {"text": "Once..."}}]}',
            'action': 'submit',
        }
        response = self.client.post(reverse('lore:create'), data)
        self.assertEqual(LorePost.objects.filter(title='New Story').count(), 1)
        new_post = LorePost.objects.get(title='New Story')
        
        # Should redirect to dashboard
        self.assertRedirects(response, reverse('users:dashboard'))
        
        # Moderation flags
        self.assertTrue(new_post.pending_approval)
        self.assertFalse(new_post.is_published)
        self.assertFalse(new_post.is_approved)
        self.assertIsNotNone(new_post.submitted_at)

    def test_lore_create_draft_workflow(self):
        """Saving a lore post as draft should not set pending_approval."""
        self.client.login(username='writer', password='password')
        data = {
            'title': 'Draft Story',
            'category': self.category.id,
            'content_json': '{"blocks": []}',
            'action': 'draft',
        }
        response = self.client.post(reverse('lore:create'), data)
        new_post = LorePost.objects.get(title='Draft Story')
        
        self.assertRedirects(response, reverse('users:dashboard'))
        self.assertFalse(new_post.pending_approval)
        self.assertFalse(new_post.is_published)
        self.assertFalse(new_post.is_approved)
        self.assertIsNone(new_post.submitted_at)

    def test_lore_edit_view(self):
        self.client.login(username='writer', password='password')
        response = self.client.get(reverse('lore:edit', kwargs={'slug': self.post.slug}))
        self.assertEqual(response.status_code, 200)
        
        data = {
            'title': 'Updated Igbo Origins',
            'category': self.category.id,
            'content_json': '{"blocks": []}',
            'action': 'submit',
        }
        response = self.client.post(reverse('lore:edit', kwargs={'slug': self.post.slug}), data)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated Igbo Origins')
        # Re-submit should reset approval
        self.assertFalse(self.post.is_approved)
        self.assertTrue(self.post.pending_approval)

    def test_lore_delete_view(self):
        """Unapproved posts can be deleted by the author."""
        self.client.login(username='writer', password='password')
        unapproved_post = LorePost.objects.create(
            title='Deletable Post', author=self.user,
            is_approved=False, is_published=False
        )
        response = self.client.get(reverse('lore:delete', kwargs={'slug': unapproved_post.slug}))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(reverse('lore:delete', kwargs={'slug': unapproved_post.slug}))
        self.assertRedirects(response, reverse('users:dashboard'))
        self.assertEqual(LorePost.objects.filter(id=unapproved_post.id).count(), 0)

    def test_lore_delete_published_blocked(self):
        """Published+approved posts cannot be deleted by non-staff."""
        self.client.login(username='writer', password='password')
        response = self.client.post(reverse('lore:delete', kwargs={'slug': self.post.slug}))
        # Should redirect back with error, post still exists
        self.assertTrue(LorePost.objects.filter(id=self.post.id).exists())


class LoreModerationTests(TestCase):
    """Test the full moderation lifecycle: create → pending → approve/reject."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='author', password='password')
        self.admin = User.objects.create_superuser(username='admin', password='password', email='admin@test.com')
        self.category = Category.objects.create(name='Folktales', slug='folktales', type='lore')

    def test_create_shows_in_moderation_dashboard(self):
        """A submitted post should appear in the moderation dashboard."""
        self.client.login(username='author', password='password')
        self.client.post(reverse('lore:create'), {
            'title': 'Pending Tale',
            'category': self.category.id,
            'content_json': '{"blocks": []}',
            'action': 'submit',
        })
        
        post = LorePost.objects.get(title='Pending Tale')
        self.assertTrue(post.pending_approval)
        
        # Check moderation dashboard
        self.client.login(username='admin', password='password')
        response = self.client.get(reverse('users:moderation_dashboard'))
        self.assertContains(response, 'Pending Tale')

    def test_approved_post_shows_in_list(self):
        """After admin approves, post should appear in the public lore list."""
        post = LorePost.objects.create(
            title='Approved Tale', author=self.user, category=self.category,
            pending_approval=True, is_published=False, is_approved=False
        )
        
        # Should NOT appear in list
        response = self.client.get(reverse('lore:list'))
        self.assertNotContains(response, 'Approved Tale')
        
        # Admin approves
        self.client.login(username='admin', password='password')
        self.client.post(reverse('users:approve_lore', kwargs={'pk': post.pk}))
        
        post.refresh_from_db()
        self.assertTrue(post.is_published)
        self.assertTrue(post.is_approved)
        self.assertFalse(post.pending_approval)
        
        # Now should appear in list
        response = self.client.get(reverse('lore:list'))
        self.assertContains(response, 'Approved Tale')
