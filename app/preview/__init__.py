from datetime import datetime
from flask import Blueprint, render_template

bp = Blueprint('preview', __name__)

MOCK_POSTS = [
    {
        'id': 1,
        'title': 'The Evolution of the Modern Scottish Kilt',
        'date': '2025-03-30',
        'author': 'nick-fiddes',
        'summary': '<p>The Scottish kilt, with its swirling tartans and cultural resonance, is a garment steeped in history, rebellion, and reinvention. Its journey from a simple Highland wrap to a symbol of national identity—and later, a global fashion statement—mirrors Scotland\'s own turbulent and triumphant narrative. This expanded exploration delves deeper into the kilt\'s evolution, tracing its transformation across ten centuries while highlighting the social, political, and artistic forces that shaped its legacy.</p>',
        'created_at': datetime(2025, 3, 30),
        'subtitle': 'From Ancient Practicality to Global Icon',
        'header_image': '/static/images/posts/kilt-evolution/kilt-evolution_header.jpg',
        'sections': [
            {
                'heading': 'Early Forms of Highland Dress (Pre-16th Century)',
                'text': "<p>Long before the iconic kilt emerged, Scotland's rugged landscapes necessitated practical clothing. Early Highlanders, including the Picts and Gaels, wore layered woollen tunics, leggings (<i>trews</i>), and cloaks (<i>brats</i>), often fastened with intricately designed brooches. These garments, crafted from coarse, undyed wool or animal hides, prioritised durability over ornamentation.</p><p>Archaeological evidence, such as the 8th-century <b>Dunfallandy Stone</b> in Perthshire, depicts figures draped in knee-length tunics and cloaks secured by penannular brooches—a style echoed in the <b>Book of Kells</b>. The <b>Lewis chessmen</b>, 12th-century carvings found in the Outer Hebrides, further illustrate the use of belted tunics, suggesting early precursors to pleated garments.</p><p>Natural dyes derived from local plants, such as <b>crottle</b> (lichen) for russet tones and <b>woad</b> for blue, introduced regional colour variations. These early textiles were not merely functional; they signified social rank. Chieftains wore finer weaves and elaborate brooches, while commoners relied on simpler designs. This period laid the groundwork for the structured, identity-driven attire that would define later Highland dress.</p>",
                'image': {
                    'src': '/static/images/posts/kilt-evolution/kilt-evolution_early-highland-dress.jpg',
                    'alt': 'Pictish warrior in tunic and brat cloak on a cliff with standing stones.',
                    'caption': 'Early Highland attire: A Pictish warrior embodying resilience in practical woollen tunic and cloak.'
                }
            },
            {
                'heading': 'Origins of the Great Kilt (16th Century)',
                'text': "<p>The <b>féileadh mòr</b> (great kilt) emerged in the late 16th century as a response to the Highlands' demanding climate and lifestyle. This versatile garment—a five- to six-metre length of tartan cloth—was pleated at the waist, secured with a leather belt, and draped over the shoulder. It served as a cloak by day and a blanket by night, epitomising the resourcefulness of Gaelic culture.</p><p>Contemporary accounts, such as those by <b>Bishop John Leslie</b> in 1578, praised its adaptability: <i>\"Their plaids protect them from the cold… and in summer, they cast off the upper part, retaining only the skirt.\"</i> Regional variations in weave and hue began to emerge, with <b>Lochaber</b> weavers producing earthy greens and browns, while <b>Aberdeenshire</b> clans favoured deeper blues.</p><p>The féileadh mòr's design also held tactical advantages. During the 1544 Battle of Loch Lochy, Highland fighters reportedly discarded their plaids mid-battle to increase mobility—a practice later romanticised in Jacobite lore.</p>",
                'image': {
                    'src': '/static/images/posts/kilt-evolution/kilt-evolution_great-kilt-origins.jpg',
                    'alt': '16th-century Highlander pleating and belting a large féileadh mòr tartan wrap.',
                    'caption': 'The versatile féileadh mòr: A 16th-century Highlander dons the great kilt for protection and practicality.'
                }
            },
            {
                'heading': 'The Kilt in the 17th and 18th Centuries',
                'text': "<p>The kilt's evolution continued through the 17th and 18th centuries, influenced by the political landscape and the rise of the clans. The <b>Jacobite Rebellions</b> of the 17th century saw the kilt as a symbol of resistance and national identity. Highlanders wore their tartans proudly, often with a <b>bonnet</b> or <b>plaid cap</b> to show their allegiance.</p><p>The <b>Highland Clearances</b> of the 19th century forced many Highlanders to migrate to the cities, where they continued to wear their tartans as a symbol of their heritage. The kilt became a symbol of resilience and cultural continuity.</p>",
                'image': {
                    'src': '/static/images/posts/kilt-evolution/kilt-evolution_highland-dress-suppression.jpg',
                    'alt': 'Highlanders migrating to the cities during the Highland Clearances',
                    'caption': 'Highlanders wearing their tartans during the Highland Clearances'
                }
            },
            {
                'heading': 'The Kilt in the 19th and 20th Centuries',
                'text': "<p>The 19th and 20th centuries saw the kilt's transformation into a global fashion statement. The <b>Highland Games</b> and <b>Celtic festivals</b> around the world celebrated the kilt's cultural significance. The kilt became a symbol of Scottish identity and pride.</p><p>The <b>Kiltwalk</b> charity event, founded in 2009, has raised over £10 million for charity, showcasing the kilt's popularity and cultural impact.</p>",
                'image': {
                    'src': '/static/images/posts/kilt-evolution/kilt-evolution_romantic-revival-renaissance.jpg',
                    'alt': 'People of all ages participating in the Kiltwalk',
                    'caption': 'People of all ages participating in the Kiltwalk'
                }
            },
            {
                'heading': 'The Kilt in the 21st Century',
                'text': "<p>In the 21st century, the kilt continues to evolve. It has become a symbol of Scottish identity and pride, worn by people around the world. The <b>Scottish Government</b> has declared the kilt as the national dress of Scotland.</p><p>The kilt's versatility and adaptability make it a symbol of heritage and innovation. It has been worn by celebrities, athletes, and everyday people, showcasing its cultural significance and versatility.</p>",
                'image': {
                    'src': '/static/images/posts/kilt-evolution/kilt-evolution_modern-innovations-fashion.jpg',
                    'alt': 'A man wearing a kilt at a wedding',
                    'caption': 'A man wearing a kilt at a wedding'
                }
            }
        ],
        'conclusion': {
            'heading': 'A Living Legacy',
            'text': "<p>The kilt's evolution—from the féileadh mòr to haute couture—encapsulates Scotland's resilience and creativity. It has been a shroud, a uniform, a protest symbol, and a canvas for art. As it adapts to the 21st century, the kilt remains not just a garment, but a narrative woven through time, thread by colourful thread. Whether on a Glasgow catwalk or a Canadian high street, it endures as a testament to heritage and innovation—a tartan tapestry still being written.</p>"
        }
    },
    {
        'id': 2,
        'title': 'The Tradition of the Scottish Quaich',
        'date': '2023-10-27',
        'author': 'caitrin-stewart',
        'summary': '<p>The <b>quaich</b>, Scotland\'s cherished <b>\"cup of friendship,\"</b> holds a special place in Scottish tradition, symbolising hospitality, unity, and trust. Originating centuries ago, its simple yet profound design—a shallow, two-handled bowl—embodies a rich history spanning <b>clan</b> gatherings, ceremonial rituals, royal celebrations, and contemporary <b>weddings</b>. This article explores the evolution of the quaich, delving into its earliest origins, cultural significance, craftsmanship, historical anecdotes, and enduring presence in modern Scottish culture.</p>',
        'created_at': datetime(2023, 10, 27),
        'subtitle': "Scotland's Cup of Friendship: From Ancient Symbol to Modern Keepsake",
        'header_image': '/static/images/site/quaich-header.jpg',
        'sections': [
            {
                'heading': 'Early Origins: Ancient Beginnings and Symbolic Meaning',
                'text': "<p>The <b>quaich</b>, derived from the Gaelic word <b>\"cuach\"</b> meaning cup, traces its origins to medieval Scotland. Archaeological evidence suggests early quaichs date back as far as the 16th century, though some theories posit even earlier roots. Initially carved from simple materials such as <b>wood</b>, <b>horn</b>, and <b>bone</b>, early quaichs represented more than mere drinking vessels; they symbolised peace, friendship, and trust, integral values within and between clans. Their distinctive <b>two-handled design</b> encouraged mutual trust, as both hands were visible, discouraging concealed weapons or hidden intentions.</p>",
                'image': {
                    'src': '/static/images/posts/quaich-traditions/quaich-traditions_early-origins-wooden.jpg',
                    'alt': 'Early hand-carved wooden quaich by a hearth',
                    'caption': 'A simple wooden quaich reflects early Highland values of peace and trust.'
                }
            },
            {
                'heading': 'The Quaich in the 17th and 18th Centuries',
                'text': "<p>The quaich's use in the 17th and 18th centuries was influenced by the political landscape and the rise of the clans. The <b>Jacobite Rebellions</b> of the 17th century saw the quaich as a symbol of resistance and national identity. Highlanders drank from their quaichs proudly, often with a <b>bonnet</b> or <b>plaid cap</b> to show their allegiance.</p><p>The <b>Highland Clearances</b> of the 19th century forced many Highlanders to migrate to the cities, where they continued to drink from their quaichs as a symbol of their heritage.</p>",
                'image': {
                    'src': '/static/images/posts/quaich-traditions/quaich-traditions_clan-unity-hospitality.jpg',
                    'alt': 'Clan gathering with quaichs',
                    'caption': 'A clan gathering sharing quaichs as a symbol of unity.'
                }
            },
            {
                'heading': 'The Quaich in the 19th and 20th Centuries',
                'text': "<p>The 19th and 20th centuries saw the quaich's transformation into a global symbol of Scottish identity and pride. The <b>Highland Games</b> and <b>Celtic festivals</b> around the world celebrated the quaich's cultural significance. The quaich became a symbol of Scottish identity and pride.</p><p>The <b>Kiltwalk</b> charity event, founded in 2009, has raised over £10 million for charity, showcasing the quaich's popularity and cultural impact.</p>",
                'image': {
                    'src': '/static/images/posts/quaich-traditions/quaich-traditions_contemporary-culture.jpg',
                    'alt': 'People of all ages participating in the Kiltwalk',
                    'caption': 'People of all ages participating in the Kiltwalk'
                }
            },
            {
                'heading': 'The Quaich in the 21st Century',
                'text': "<p>In the 21st century, the quaich continues to evolve. It has become a symbol of Scottish identity and pride, worn by people around the world. The <b>Scottish Government</b> has declared the quaich as the national drink of Scotland.</p><p>The quaich's versatility and adaptability make it a symbol of heritage and innovation. It has been drunk by celebrities, athletes, and everyday people, showcasing its cultural significance and versatility.</p>",
                'image': {
                    'src': '/static/images/posts/quaich-traditions/quaich-traditions_modern-diplomacy.jpg',
                    'alt': 'A man drinking from a quaich at a wedding',
                    'caption': 'A man drinking from a quaich at a wedding'
                }
            }
        ],
        'conclusion': {
            'heading': 'Conclusion: The Enduring Power of the Quaich',
            'text': "<p>From humble beginnings as a simple wooden cup to a sophisticated emblem of Scottish hospitality and friendship, the <b>quaich\'s</b> journey symbolises Scotland's resilience and cultural continuity. Its evolution mirrors Scotland's own history, shaped by tradition, turmoil, revival, and adaptation. Today, whether shared during intimate family gatherings or offered ceremonially on the global stage, the quaich remains an enduring, powerful emblem of unity and goodwill. This tradition continues to remind Scots and non-Scots alike of the lasting power of simple gestures to strengthen bonds and celebrate friendship across generations.</p>"
        }
    }
]

@bp.route('/')
def listing():
    return render_template('preview/listing.html', posts=MOCK_POSTS)

@bp.route('/<int:post_id>/')
def post_detail(post_id):
    post = next((p for p in MOCK_POSTS if p['id'] == post_id), None)
    if not post:
        return 'Post not found', 404
    return render_template('preview/post_preview.html', post=post) 