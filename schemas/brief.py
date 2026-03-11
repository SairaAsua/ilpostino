from pydantic import BaseModel


class GoogleFormData(BaseModel):
    user_id: str
    name: str
    bio: str
    projects: list[str]
    links: list[str]
    style_preferences: str
    photo_urls: list[str] = []


class Project(BaseModel):
    name: str
    description: str
    url: str = ""
    status: str = ""


class SocialLink(BaseModel):
    platform: str
    url: str


class InitialBlogPost(BaseModel):
    title: str
    excerpt: str
    body: str
    date: str = ""


class StructuredBrief(BaseModel):
    user_id: str
    full_name: str
    headline: str
    bio_paragraphs: list[str]
    projects: list[Project]
    social_links: list[SocialLink]
    tone: str
    style_keywords: list[str]
    photo_urls: list[str] = []
    initial_blog_posts: list[InitialBlogPost] = []


class DesignTokens(BaseModel):
    primary_color: str
    accent_color: str
    background_color: str
    text_color: str
    font_heading: str
    font_body: str
    layout: str
