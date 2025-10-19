from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock


class HomePage(Page):
    """Home page model"""
    hero_title = models.CharField(max_length=255, default="Door to Door LPG Gas Delivery")
    hero_subtitle = models.CharField(max_length=500, blank=True)
    hero_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    
    # Features section
    features_title = models.CharField(max_length=255, default="Why Choose Alpha LPGas")
    features = StreamField([
        ('feature', blocks.StructBlock([
            ('icon', blocks.CharBlock(required=False, help_text="Icon class or emoji")),
            ('title', blocks.CharBlock()),
            ('description', blocks.TextBlock()),
        ])),
    ], use_json_field=True, blank=True)
    
    # Call to action
    cta_title = models.CharField(max_length=255, default="Ready to Order?")
    cta_text = RichTextField(blank=True)
    cta_button_text = models.CharField(max_length=100, default="Order Now")
    cta_button_link = models.CharField(max_length=500, default="/shop")
    
    content_panels = Page.content_panels + [
        FieldPanel('hero_title'),
        FieldPanel('hero_subtitle'),
        FieldPanel('hero_image'),
        FieldPanel('features_title'),
        FieldPanel('features'),
        FieldPanel('cta_title'),
        FieldPanel('cta_text'),
        FieldPanel('cta_button_text'),
        FieldPanel('cta_button_link'),
    ]

    class Meta:
        verbose_name = "Home Page"


class ContentPage(Page):
    """Generic content page (About, Contact, etc.)"""
    body = StreamField([
        ('heading', blocks.CharBlock(form_classname="title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('quote', blocks.BlockQuoteBlock()),
        ('list', blocks.ListBlock(blocks.CharBlock())),
    ], use_json_field=True)
    
    content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]

    class Meta:
        verbose_name = "Content Page"


class BlogIndexPage(Page):
    """Blog listing page"""
    intro = RichTextField(blank=True)
    
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        blog_posts = self.get_children().live().order_by('-first_published_at')
        context['blog_posts'] = blog_posts
        return context

    class Meta:
        verbose_name = "Blog Index Page"


class BlogPost(Page):
    """Individual blog post"""
    date = models.DateField("Post date")
    intro = models.CharField(max_length=500)
    body = StreamField([
        ('heading', blocks.CharBlock(form_classname="title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('quote', blocks.BlockQuoteBlock()),
    ], use_json_field=True)
    
    featured_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    
    content_panels = Page.content_panels + [
        FieldPanel('date'),
        FieldPanel('intro'),
        FieldPanel('featured_image'),
        FieldPanel('body'),
    ]

    class Meta:
        verbose_name = "Blog Post"
