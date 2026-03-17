from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel
from wagtail.search import index
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.api import APIField


class BlogIndexPage(Page):
    intro = RichTextField(blank=True)
    
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]
    
    api_fields = [
        APIField('intro'),
    ]
    
    def get_context(self, request):
        context = super().get_context(request)
        blogpages = self.get_children().live().order_by('-first_published_at')
        context['blogpages'] = blogpages
        return context
    
    class Meta:
        verbose_name = "Blog Index Page"


class BlogPage(Page):
    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)
    body = StreamField([
        ('heading', blocks.CharBlock(form_classname="title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('code', blocks.TextBlock()),
    ], use_json_field=True, blank=True)
    
    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]
    
    content_panels = Page.content_panels + [
        FieldPanel('date'),
        FieldPanel('intro'),
        FieldPanel('body'),
    ]
    
    api_fields = [
        APIField('date'),
        APIField('intro'),
        APIField('body'),
    ]
    
    class Meta:
        verbose_name = "Blog Page"
