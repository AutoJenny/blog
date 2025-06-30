"""LangChain integration for content generation and enhancement."""

from typing import Dict, List, Optional
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain.chains import LLMChain
from pydantic import BaseModel, Field
import json

class ContentIdea(BaseModel):
    """Schema for content idea generation."""
    title: str = Field(description="Engaging title for the blog post")
    summary: str = Field(description="Brief summary of the post content")
    sections: List[Dict] = Field(description="List of sections with titles and brief descriptions")
    target_audience: List[str] = Field(description="Target audience segments")
    keywords: List[str] = Field(description="SEO keywords")

class ContentExpansion(BaseModel):
    """Schema for section content expansion."""
    content: str = Field(description="Expanded content for the section")
    social_media_snippets: Dict = Field(description="Platform-specific content versions")
    keywords: List[str] = Field(description="Relevant keywords for the section")

def create_idea_generation_chain() -> LLMChain:
    """Create a chain for generating blog post ideas."""
    prompt = PromptTemplate(
        input_variables=["topic", "style", "audience"],
        template="""Generate a detailed blog post idea about {topic} in a {style} style for {audience}.
        
        The response should be structured and engaging, focusing on Scottish heritage and culture.
        Include specific sections that could be repurposed for social media.
        
        {format_instructions}
        """
    )
    
    parser = PydanticOutputParser(pydantic_object=ContentIdea)
    model = ChatOpenAI(temperature=0.7)
    
    return LLMChain(
        llm=model,
        prompt=prompt.partial(format_instructions=parser.get_format_instructions()),
        output_parser=parser
    )

def create_content_expansion_chain() -> LLMChain:
    """Create a chain for expanding section content."""
    prompt = PromptTemplate(
        input_variables=["title", "summary", "tone", "platforms"],
        template="""Expand the following section into detailed content:
        
        Title: {title}
        Summary: {summary}
        Tone: {tone}
        Target Platforms: {platforms}
        
        Create engaging content that can be repurposed across different platforms while maintaining
        authenticity and cultural accuracy for Scottish heritage content.
        
        {format_instructions}
        """
    )
    
    parser = PydanticOutputParser(pydantic_object=ContentExpansion)
    model = ChatOpenAI(temperature=0.5)
    
    return LLMChain(
        llm=model,
        prompt=prompt.partial(format_instructions=parser.get_format_instructions()),
        output_parser=parser
    )

def create_seo_optimization_chain() -> LLMChain:
    """Create a chain for SEO optimization suggestions."""
    prompt = PromptTemplate(
        input_variables=["content", "keywords"],
        template="""Analyze and optimize the following content for SEO:
        
        Content: {content}
        Target Keywords: {keywords}
        
        Provide suggestions for:
        1. Title optimization
        2. Meta description
        3. Header structure
        4. Keyword placement
        5. Internal linking opportunities
        
        Focus on Scottish heritage and cultural authenticity while maintaining SEO best practices.
        """
    )
    
    model = ChatOpenAI(temperature=0.3)
    return LLMChain(llm=model, prompt=prompt)

def generate_social_media_content(section: PostSection, platforms: List[str]) -> Dict:
    """Generate platform-specific content from a post section.
    
    Args:
        section: PostSection object containing the content
        platforms: List of target platforms (e.g., ['tiktok', 'instagram'])
        
    Returns:
        Dict containing platform-specific content versions
    """
    prompt = PromptTemplate(
        input_variables=["content", "title", "platforms"],
        template="""Transform the following content for social media platforms: {platforms}
        
        Title: {title}
        Content: {content}
        
        For each platform, create:
        1. Engaging captions
        2. Relevant hashtags
        3. Content structure
        4. Key talking points
        
        Maintain Scottish cultural authenticity while optimizing for each platform's format.
        """
    )
    
    model = ChatOpenAI(temperature=0.6)
    chain = LLMChain(llm=model, prompt=prompt)
    
    result = chain.run(
        content=section.content,
        title=section.title,
        platforms=", ".join(platforms)
    )
    
    return json.loads(result) if isinstance(result, str) else result 