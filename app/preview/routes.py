from flask import Blueprint, render_template

preview = Blueprint('preview', __name__)

@preview.route('/preview/')
def preview_listing():
    # Mock data for visual prototype
    posts = [
        {
            'id': 1,
            'title': 'The History of the Kilt',
            'date': '2024-05-01',
            'author': 'Nick Fiddes',
            'summary': 'A deep dive into the origins and evolution of the Scottish kilt.'
        },
        {
            'id': 2,
            'title': 'Quaich Traditions',
            'date': '2024-04-15',
            'author': 'Jane MacLeod',
            'summary': 'Exploring the meaning and rituals behind the Scottish quaich.'
        }
    ]
    return render_template('preview_listing.html', posts=posts)

@preview.route('/preview/<int:post_id>/')
def preview_post(post_id):
    # Mock data for visual prototype
    post = {
        'id': post_id,
        'title': 'The History of the Kilt',
        'date': '2024-05-01',
        'author': 'Nick Fiddes',
        'summary': 'A deep dive into the origins and evolution of the Scottish kilt.',
        'subtitle': 'From ancient times to modern fashion',
        'header_image': '/static/kilt-header.jpg',
        'sections': [
            {'heading': 'Origins', 'text': 'The kilt has its roots in...'},
            {'heading': 'Evolution', 'text': 'Over the centuries, the kilt...'}
        ],
        'tags': ['history', 'fashion', 'Scotland'],
        'footer': 'Thanks for reading!'
    }
    return render_template('preview_post.html', post=post) 