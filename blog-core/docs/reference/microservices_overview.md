# Microservices Architecture Overview

## System Architecture

The blog system has evolved from a monolithic application to a microservices architecture with the following components:

### Core Services

1. **blog-core** (`http://localhost:5001`)
   - Main application server
   - Workflow management system
   - Content management interface
   - Database management
   - API gateway for microservices

2. **blog-llm-actions** (`http://localhost:5002`)
   - LLM processing microservice
   - Purple-themed interface
   - Full LLM functionality API
   - Action execution engine
   - Prompt processing system

### Database Architecture

- **Unified PostgreSQL Database**: All services share the same PostgreSQL database
- **No Service-Specific Tables**: No separate database tables for microservices
- **Shared Schema**: All services use the existing blog database schema
- **Direct SQL Access**: All services use psycopg2 for direct database access

## Service Communication

### API-Based Communication
- **RESTful APIs**: All inter-service communication via HTTP APIs
- **CORS Enabled**: Cross-origin requests enabled between services
- **JSON Data Format**: All API responses in JSON format
- **Standard HTTP Status Codes**: Consistent error handling across services

### Service Discovery
- **Health Check Endpoints**: Each service provides `/health` endpoint
- **Status Monitoring**: blog-core monitors microservice health
- **Graceful Degradation**: System continues working if microservices are unavailable

## Access Points

### blog-core (Main Application)
- **Main Interface**: `http://localhost:5001/`
- **Workflow System**: `http://localhost:5001/workflow/`
- **Settings**: `http://localhost:5001/settings/`
- **API Documentation**: `http://localhost:5001/docs/`
- **Health Check**: `http://localhost:5001/health`

### blog-llm-actions (LLM Microservice)
- **Main Interface**: `http://localhost:5002/`
- **Test Page**: `http://localhost:5002/test`
- **API Base**: `http://localhost:5002/api/`
- **Health Check**: `http://localhost:5002/health`
- **Static Files**: `http://localhost:5002/static/`

## Integration Points

### Workflow Integration
- **Microservice Embedding**: blog-core embeds microservices in workflow pages
- **Content Areas**: Designated areas in workflow templates for microservice content
- **API Communication**: JavaScript-based communication between services
- **Context Sharing**: Shared session and context data between services
- **Iframe Communication**: postMessage API for cross-iframe data exchange

### Iframe Communication Architecture
- **postMessage API**: Secure cross-origin communication between iframes
- **Message Types**: Standardized message types for different operations
- **Timeout Handling**: Graceful fallback for communication failures
- **Error Recovery**: Continue operation if iframe communication fails

#### Sections Substage Communication
- **Purple Panel (LLM Actions)**: Requests selected section IDs from green panel
- **Green Panel (Sections)**: Responds with array of checked section IDs
- **Section Processing**: Purple panel processes each selected section individually
- **Context Integration**: Section-specific data included in LLM prompts

### LLM Integration
- **Action Execution**: blog-core calls blog-llm-actions for LLM processing
- **Prompt Management**: Centralized prompt templates in database
- **Model Configuration**: Shared LLM model and provider configuration
- **Result Processing**: Structured output handling and field mapping

#### Substage-Specific Processing
- **Post Info Stage**: Processes post-level data (title, subtitle, etc.)
- **Sections Stage**: Processes individual sections with section-specific context
- **Other Stages**: Processes development-level data (basic_idea, idea_scope, etc.)

#### Sections Substage Behavior
- **Section Selection**: Reads checkbox selections from sections panel
- **Individual Processing**: Processes each selected section separately
- **Context Enhancement**: Includes section-specific data in LLM prompts
- **Targeted Saving**: Saves results to each section's specific field
- **Progress Tracking**: Shows progress for multiple section processing

## Development Guidelines

### Service Development
1. **Independent Deployment**: Each service can be developed and deployed independently
2. **API-First Design**: All functionality exposed via REST APIs
3. **CORS Configuration**: Enable cross-origin requests for integration
4. **Health Endpoints**: Implement `/health` endpoint for monitoring
5. **Error Handling**: Consistent error response format

### Integration Development
1. **JavaScript Communication**: Use fetch API for inter-service communication
2. **Event Handling**: Implement proper error handling for service failures
3. **Loading States**: Provide user feedback during service communication
4. **Fallback Behavior**: Graceful degradation when services are unavailable

### Database Access
1. **Shared Connection**: Use same database connection string across services
2. **Direct SQL**: Use psycopg2 for all database operations
3. **Schema Consistency**: Maintain consistent database schema across services
4. **Transaction Management**: Proper transaction handling for data integrity

## Security Considerations

### CORS Configuration

#### blog-core
- **Allowed Origins**: `http://localhost:5001`
- **Methods**: GET, POST, PUT, DELETE, OPTIONS
- **Headers**: Content-Type, Authorization

#### blog-llm-actions
- **Allowed Origins**: 
  - `http://localhost:5001` (blog-core)
  - `http://localhost:5002` (blog-llm-actions)
- **Methods**: GET, POST, PUT, DELETE, OPTIONS
- **Headers**: Content-Type, Authorization

#### blog-post-sections
- **Allowed Origins**: 
  - `http://localhost:5000` (blog-core)
  - `http://localhost:5001` (blog-core)
  - `http://localhost:5002` (blog-llm-actions)
  - `http://localhost:5003` (blog-post-sections)
- **Methods**: GET, POST, PUT, DELETE, OPTIONS
- **Headers**: Content-Type, Authorization

### API Security

### API Security
- **Input Validation**: Validate all API inputs
- **Error Handling**: Don't expose sensitive information in error messages
- **Rate Limiting**: Implement rate limiting for API endpoints
- **Authentication**: Consider authentication for sensitive operations

## Monitoring and Debugging

### Health Monitoring
- **Health Checks**: Regular health check polling
- **Status Display**: Show service status in UI
- **Error Reporting**: Log service communication errors
- **Performance Monitoring**: Track API response times

### Debugging Tools
- **API Test Pages**: Dedicated test interfaces for each service
- **Logging**: Comprehensive logging across all services
- **Error Tracking**: Centralized error tracking and reporting
- **Development Tools**: Browser developer tools for API debugging

## Deployment Considerations

### Service Dependencies
- **Database**: Ensure PostgreSQL is running and accessible
- **Ollama**: LLM service requires Ollama for model execution
- **Port Management**: Avoid port conflicts between services
- **Environment Variables**: Consistent environment configuration

### Scaling Considerations
- **Load Balancing**: Consider load balancing for high-traffic scenarios
- **Service Discovery**: Implement service discovery for dynamic scaling
- **Database Connection Pooling**: Optimize database connections
- **Caching**: Implement caching for frequently accessed data

## Migration from Monolithic

### Backward Compatibility
- **API Compatibility**: Maintain compatibility with existing API endpoints
- **Data Migration**: No data migration required (shared database)
- **Feature Parity**: Ensure all existing features work in new architecture
- **User Experience**: Maintain consistent user experience

### Gradual Migration
- **Feature-by-Feature**: Migrate features one at a time
- **Testing**: Comprehensive testing at each migration step
- **Rollback Plan**: Ability to rollback to previous architecture
- **Documentation**: Update documentation as architecture evolves

## Future Considerations

### Additional Microservices
- **Image Processing**: Dedicated image processing service
- **Content Generation**: Specialized content generation service
- **Analytics**: Analytics and reporting service
- **Notification**: Notification and alerting service

### Advanced Features
- **Service Mesh**: Consider service mesh for advanced networking
- **API Gateway**: Centralized API gateway for external access
- **Event Streaming**: Event-driven architecture for real-time updates
- **Container Orchestration**: Kubernetes or Docker Compose for deployment

## Related Documentation

- [LLM Actions Microservice API](api/current/llm_actions.md)
- [Workflow System Integration](workflow/README.md)
- [Database Schema](database/schema.md)
- [API Reference](api/README.md)
- [Deployment Guide](DEPLOYMENT.md) 