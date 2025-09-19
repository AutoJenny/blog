# Syndication System User Guide

## Quick Start Guide

### How to Generate Facebook Posts from Blog Content

1. **Navigate to the Facebook Feed Post Page**
   - Go to `http://localhost:5001/syndication/facebook/feed_post`

2. **Select a Blog Post**
   - Choose a published blog post from the dropdown
   - The system will display all available sections

3. **Generate Content**
   - Click the "Generate all [X] sections" button
   - Watch the progress bar as each section is processed
   - Wait for completion (usually 1-2 minutes for 6-7 sections)

4. **Review Results**
   - Generated Facebook posts appear in the "AI Content Generation" panel
   - Each post shows the section title and generated content
   - Posts are automatically saved to the database

## What Gets Generated

### Content Format
- **Length**: 150-200 characters (optimized for Facebook)
- **Tone**: Conversational and engaging
- **Hashtags**: Exactly 3 relevant hashtags at the end
- **Call-to-Action**: Clear invitation to engage
- **Style**: Clean, professional, brand-appropriate

### Example Output
```
🏴󠁧󠁢󠁳󠁣󠁴󠁿 Delve into the vibrant world of Scottish storytelling! From ancient oral traditions to modern literature, discover how stories continue to enrich our lives in Scotland today. #ScottishStories #ContemporaryLiterature #OralTraditions 📚✨ #StorytellingCommunity #ModernNarratives
```

## Understanding the Interface

### Item Selection Panel
- **Post Dropdown**: Lists all published blog posts
- **Section List**: Shows available sections with titles and previews
- **Generate Button**: Processes all sections when clicked
- **Progress Bar**: Shows real-time processing status

### AI Content Generation Panel
- **Results Display**: Shows all generated Facebook posts
- **Section Headers**: Each post labeled with its source section
- **Status Badges**: Visual indicators of generation status
- **Timestamps**: When each post was generated

## Troubleshooting

### Common Issues

**"No sections found for this post"**
- Ensure the blog post has published sections
- Check that the post status is "published"

**"Generate all sections" button is disabled**
- Select a blog post first
- Ensure the post has sections available

**Generation fails or stops**
- Check that Ollama is running on your system
- Verify database connection
- Try refreshing the page and starting again

**Generated content seems poor quality**
- The AI uses the section content as input
- Ensure blog sections have sufficient content
- Check that section titles are descriptive

### Getting Help

1. **Check the logs**: Look at the browser console for error messages
2. **Verify services**: Ensure Ollama and database are running
3. **Try again**: Most issues resolve with a page refresh
4. **Contact support**: Refer to technical documentation for advanced issues

## Best Practices

### For Better Results
- **Choose posts with rich content**: More detailed sections produce better posts
- **Use descriptive section titles**: These help the AI understand context
- **Review generated content**: Always check posts before using them
- **Process in batches**: Don't try to generate too many posts at once

### Content Guidelines
- **Keep sections focused**: Single-topic sections work best
- **Use clear titles**: Descriptive section titles improve AI understanding
- **Include context**: Background information helps generate relevant posts
- **Avoid very short sections**: At least 2-3 sentences work best

## Advanced Features

### Database Storage
- All generated content is permanently saved
- Full metadata is stored for tracking and analysis
- Content can be retrieved and reused later
- Processing history is maintained

### API Access
- Generated content available via REST API
- Metadata includes source post, section, and generation details
- Can be integrated with other systems
- Supports bulk operations

### Customization
- Prompt templates can be modified for different styles
- LLM settings can be adjusted for different outputs
- Platform-specific rules can be configured
- Content length and format can be customized

## System Requirements

### Technical Requirements
- **Ollama**: Must be running with Mistral model
- **Database**: PostgreSQL with proper schema
- **Browser**: Modern browser with JavaScript enabled
- **Network**: Stable internet connection

### Performance
- **Processing Speed**: ~10-15 seconds per section
- **Memory Usage**: Minimal impact on system resources
- **Database**: Efficient storage with proper indexing
- **Scalability**: Can handle multiple concurrent users

## Support and Maintenance

### Regular Maintenance
- **Database Cleanup**: Old content can be archived
- **Log Management**: Logs are rotated automatically
- **Performance Monitoring**: System health is tracked
- **Updates**: Regular updates and improvements

### Getting Support
- **Documentation**: Comprehensive guides available
- **Logs**: Detailed error information in system logs
- **API Status**: Monitor endpoint health
- **Community**: Share experiences and solutions

---

*This user guide is part of the Blog Launchpad syndication system. For technical details, see the [Content Generation System](content_generation_system.md) documentation.*
