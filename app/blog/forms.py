from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class PostForm(FlaskForm):
    """Form for creating and editing blog posts."""
    title = StringField('Title', validators=[
        DataRequired(),
        Length(max=200, message='Title must be less than 200 characters')
    ])
    
    summary = TextAreaField('Summary', validators=[
        DataRequired(),
        Length(max=500, message='Summary must be less than 500 characters')
    ])
    
    content = TextAreaField('Content', validators=[
        DataRequired(),
        Length(min=100, message='Content must be at least 100 characters')
    ])
    
    categories = SelectMultipleField('Categories', 
        validators=[DataRequired(message='At least one category is required')],
        coerce=int
    )
    
    tags = StringField('Tags', validators=[Optional()])
    
    header_image = FileField('Header Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    
    submit = SubmitField('Create Post') 