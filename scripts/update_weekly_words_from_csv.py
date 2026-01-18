#!/usr/bin/env python3
"""
Update weekly words in calendar_ideas from CSV data
Overwrites existing content with new data including usage examples and provenance
"""

import os
import sys
import csv
import logging
from typing import Dict, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# CSV data provided by user
CSV_DATA = """word,translation,usage1,usage2,provenance
braw,fine; excellent,"That's a braw jacket ye've got.","The weather's been braw the day.","Pan-Scots; common in speech and writing from 18th–21st c"
gloamin,twilight,"They walked hame in the gloamin.","The hills look bonnie in the gloamin.","Poetic and literary Scots; Lowlands and Highlands; 18th–21st c"
dreich,bleak; drizzly,"It's a dreich mornin again.","The match was cancelled in the dreich weather.","Pan-Scots; especially Lowlands; 19th–21st c"
scunner,disgust; annoyance,"That film gied me a scunner.","I've a scunner for that place noo.","Pan-Scots noun/verb; attested 18th c onwards"
wee,small,"Haud on a wee minute.","She's just a wee lassie.","Pan-Scots; everyday speech; long-standing usage"
muckle,large,"That's a muckle stane.","He's got muckle energy.","Older Scots; Lowlands and Borders; 16th–19th c, now dialectal"
bairn,child,"She's awa tae pick up the bairn.","The bairns are playin in the street.","Pan-Scots; core vocabulary since Middle Scots"
ken,know,"I dinna ken where he went.","Ken ye this song?","Pan-Scots verb; core Scots usage since medieval period"
aye,yes,"Aye, I'll dae it.","Aye, that's the one.","Pan-Scots; everyday affirmative; historic and modern"
wheesht,be quiet,"Wheesht now, the show's startin.","Gie it a wheesht for a meenit.","Central Belt and Lowlands; 19th–21st c"
blether,chat; ramble,"We had a guid blether last night.","Stop bletherin and get on.","Pan-Scots; 18th–21st c"
couthie,warm; friendly,"They're a couthie couple.","It's a couthie wee place.","Lowland Scots; 18th–20th c; now less common"
gallus,bold; cheeky,"He's a gallus lad.","That gallus attitude'll get ye in trouble.","Urban Scots; especially West/Central; late 20th–21st c"
hackit,ugly,"That's a hackit hat.","He made a hackit face at me.","Lowland Scots; older descriptive adjective"
clarty,muddy,"Don't come in wi thae clarty boots.","The field was clarty efter the rain.","Pan-Scots; rural and urban; 18th–21st c"
hoachin,teeming; crowded,"The place was hoachin wi folk.","The market's hoachin every Saturday.","Urban Scots; Glasgow/Central; 20th–21st c"
stooshie,commotion,"There was a stooshie at the pub.","What's the stooshie aboot this time?","Urban Scots; 20th–21st c"
girn,complain; whine,"Stop girnin and help.","He's aye girnin aboot his work.","Pan-Scots verb; 18th–21st c"
greet,cry,"The wean's greetin again.","I nearly gret at the news.","Pan-Scots; older verb form; still common"
laldy,energy; vigour,"Gie it laldy on the dance floor.","They sang wi real laldy.","Central Belt Scots; late 20th–21st c"
lochan,small lake,"We camped by a quiet lochan.","The lochan froze ower in winter.","Highlands and literary Scots; long-standing usage"
burn,stream,"They crossed the burn by the stane bridge.","There's trout in that burn.","Pan-Scots; core geographic term"
clang,meadow,"They walked through the clang at dawn.","The cattle grazed in the lower clang.","Rural Lowland Scots; older agricultural term"
guddle,muddle; mess,"The drawer's a right guddle.","We guddled aboot in the shed for tools.","Pan-Scots; 18th–21st c"
brawlie,nicely; well,"He's daein brawlie at school.","The cake turned out brawlie.","Diminutive form; Lowlands; 19th–21st c"
fankle,tangle,"My shoelaces are in a fankle.","Don't fankle the wires.","Pan-Scots; older verb/noun; 18th–21st c"
sneck,door latch,"Lift the sneck tae open it.","The sneck's stuck again.","Lowland Scots; traditional domestic term"
swith,quickly,"Swith, get yer coat!","Swith awa or we'll be late.","Older Scots adverb; now dialectal"
thole,endure,"I canna thole this heat.","Ye'll just hae tae thole it.","Older Scots verb; literary and dialectal survival"
swither,hesitate,"Don't swither—just choose.","She swithered ower the decision.","Pan-Scots; common metaphorical use"
scaldie,seagull,"A scaldie stole my chips.","Watch the scaldies at the harbour.","Coastal Scots; East and West; 19th–21st c"
canny,careful; shrewd,"Be canny wi yer money.","He's a canny worker.","Pan-Scots; common adjective"
crabbit,bad-tempered,"He's aye crabbit in the mornin.","A crabbit look crossed her face.","Pan-Scots; 19th–21st c"
fash,bother; trouble,"Dinna fash yersel.","Sorry to fash ye wi this.","Older Scots verb; Lowlands; 18th–21st c"
kirk,church,"They gaed tae the kirk on Sunday.","The auld kirk bell rang oot.","Pan-Scots; core ecclesiastical term"
haver,talk nonsense,"Stop haverin and tell the truth.","He's aye haverin aboot somethin daft.","Pan-Scots; verb and noun; 18th–21st c"
lum,chimney,"Smoke's pourin frae the lum.","Clean the lum afore winter.","Lowland Scots; traditional domestic term"
mauchter,strength; stamina,"It took some mauchter to lift that.","She's lost a bit o mauchter lately.","Older Scots; now dialectal"
owerby,upstairs,"He's owerby in his room.","The cat's sleepin owerby.","Lowland Scots; domestic usage"
peely-wally,pale; sickly,"You're lookin awfy peely-wally.","She felt peely-wally efter the flu.","Pan-Scots; informal descriptive term"
speir,ask; inquire,"Speir at the desk for help.","I speired what time they'd arrive.","Older Scots verb; literary and dialectal survival"
skelp,slap; smack,"He fell and skelped his knee.","The rain skelped off the windows.","Pan-Scots; literal and figurative use"
shoogle,shake; wobble,"This table's fair shoogly.","Give it a wee shoogle.","Central and Lowland Scots; 19th–21st c"
boak,nausea; retch,"That smell gied me the boak.","I nearly boaked at it.","Urban Scots; West/Central; 20th–21st c"
clipe,tell-tale; snitch,"Don't be a clipe.","He clyped on his pal at school.","Lowland Scots; older moral term"
craw,boast,"He's aye crawin aboot his car.","Stop yer crawin.","Older Scots; now dialectal"
trauchle,exhaust; struggle,"I was trauchled efter the shift.","That hike fair trauchled us.","North-East and Borders Scots"
stoat,stagger; bounce,"He stoated hame fae the pub.","The ba stoated aff the waw.","Urban Scots; Central Belt"
haar,sea fog,"The haar rolled in quick.","Ye can hardly see in this haar.","East Coast Scots; longstanding meteorological term"
oxter,armpit,"He held the bag in his oxter.","Tickled under the oxters.","Pan-Scots; everyday body term"
heid,head,"Use yer heid.","He's a smart heid on him.","Pan-Scots; core vocabulary"
cloot,cloth; rag,"Gie that a wipe wi a cloot.","The cloot's aw torn.","Lowland Scots; domestic usage"
dook,dip; bathe,"Fancy a dook in the sea?","We dooked the apples.","Pan-Scots; everyday verb"
fly,cunning; sly,"He's a fly character.","That was a fly wee trick.","Urban Scots; 20th–21st c"
bummle,bumble; wander,"We bummled roon the toon.","He's aye bummlein aboot.","Modern Scots colloquialism"
carlach,snarl; sharp cry,"The dog let oot a carlach.","A carlach startled us in the dark.","Older Scots; now rare"
skreigh,screech; cry,"A skreigh echoed ower the hills.","She skreighed when she saw the spider.","Literary and dialect Scots; 18th–21st c"
claggy,sticky; gooey,"The path was claggy wi mud.","The toffee's awfy claggy.","Pan-Scots; descriptive adjective"
drookit,soaking wet,"I came hame drookit.","You're drookit—get a towel.","Pan-Scots; very common"
scunnert,fed up; disgusted,"I'm scunnert wi this weather.","He looked pure scunnert at the news.","Derived from scunner; modern Scots usage"
wanchancy,unlucky; risky,"That's a wanchancy plan.","He's a wanchancy sort.","Older Scots; Lowlands; now rare"
glaikit,foolish; scatterbrained,"Don't be glaikit.","A glaikit look crossed his face.","Pan-Scots; 18th–21st c"
smeddum,spirit; vigour,"She's full o smeddum.","It'll take smeddum to finish this.","Literary Scots; revived modern interest"
tattie,potato,"Put the tatties on.","A bag o tatties fell ower.","Pan-Scots; everyday noun"
neb,nose,"Mind yer neb.","His neb was reddened by the cold.","Urban Scots; 20th–21st c"
stour,dust; turmoil,"A stour rose behind the car.","The place was in a stour.","Older Scots; poetic and dialectal"
claver,idle chat,"We had a richt claver.","Stop yer claverin.","Pan-Scots; 18th–21st c"
dicht,clean; wipe,"Dicht the table first.","She dichted her hands.","Older Scots verb; Lowlands"
skyt,throw; fling,"He skytit the ball ower the fence.","Don't skyt that at me!","Urban Scots; Central Belt"
birl,spin; whirl,"Gie it a birl.","They birled roon the floor.","Pan-Scots; dance and motion contexts"
glisk,brief glimpse,"I got a glisk o the sun.","A glisk o movement caught my eye.","Poetic Scots; 18th–21st c"
hansel,first gift; token,"A hansel for yer new hoose.","They gave the bairn a hansel.","Traditional Scots; social custom term"
scraffle,struggle; scramble,"We scraffled up the slope.","The hens were scrafflin aboot.","Rural Scots; 19th–21st c"
coorie,curl up; nestle,"Coorie in by the fire.","We cooried doon for the night.","Pan-Scots; revived modern popularity"
dumfoonert,astonished,"I was dumfoonert at the result.","She stood there dumfoonert.","Pan-Scots; expressive adjective"
fouter,fiddle; mess about,"Stop fouterin wi that.","He foutered till it broke.","Lowland Scots; everyday verb"
raucle,hoarse,"His voice was raucle wi shoutin.","A raucle song rang oot.","Literary and dialect Scots"
rammy,row; fight,"There was a rammy ootside.","Don't start a rammy.","Urban Scots; 20th–21st c"
skail,scatter; spill,"Don't skail the milk.","The crowd skailt quickly.","Older Scots verb; rural/urban"
stot,bounce,"The ba stotted aff the flair.","It stotted again the wa.","Pan-Scots; physical motion verb"
yaffle,scold; chatter,"She yaffled at the dug.","He yaffles on aboot politics.","North-East and Central Scots"
yowes,sheep,"The yowes are in the field.","He counted yowes till he slept.","Rural Scots; traditional pastoral term"
mense,decency; dignity,"Hae some mense.","That's no very mensefu.","Older Scots moral term"
loup,leap; jump,"Loup ower the gate.","The cat louped onto the bed.","Pan-Scots; core verb"
aitch,itch,"I've an aitch on my arm.","He was aitchin aw mornin.","Scots phonological form; everyday speech"
haverel,fool,"Ye daft haverel!","Don't listen tae that haverel.","Older Scots noun; 18th–20th c"
skiver,coward; useless person,"He's a right skiver.","Don't be a skiver the day.","Modern Scots/UK slang"
breenge,charge forward,"He breenged through the door.","The dug breenged at the postie.","Urban Scots; late 20th–21st c"
girnel,grain store,"The girnel wis fu.","He checked the girnel again.","Traditional Scots rural term"
hough,thigh,"My hough's sair.","Mind yer houghs on the climb.","Older Scots anatomical term"
scart,scratch,"Gie's a scart.","She scartit her arm.","Pan-Scots; everyday verb"
wame,belly,"My wame's rummlin.","A fu wame makes a happy man.","Pan-Scots; traditional body term"
bield,shelter,"Find a bield frae the wind.","We sat in the bield o the wall.","Pan-Scots; rural and urban"
cauld,cold,"It's awfy cauld the day.","The water was cauld as ice.","Pan-Scots; phonological form"
snell,biting; sharp,"A snell wind blew in.","It's a snell mornin.","Scots adjective; older and modern use"
"""


def parse_csv_data(csv_string: str) -> List[Dict]:
    """Parse CSV string into list of dictionaries"""
    reader = csv.DictReader(csv_string.strip().split('\n'))
    return list(reader)


def format_description(translation: str, usage1: str, usage2: str, provenance: str) -> str:
    """Format idea_description with Translation, Usage examples, and Provenance"""
    parts = []
    
    # Translation
    if translation:
        parts.append(f"Translation: {translation}")
    
    # Usage examples
    usage_parts = []
    if usage1:
        usage_parts.append(f"Usage: {usage1}")
    if usage2:
        usage_parts.append(f"Usage: {usage2}")
    
    if usage_parts:
        parts.extend(usage_parts)
    
    # Provenance
    if provenance:
        parts.append(f"Provenance: {provenance}")
    
    return " | ".join(parts)


def update_weekly_words():
    """Update calendar_ideas with new weekly word data"""
    words_data = parse_csv_data(CSV_DATA)
    
    logger.info(f"Processing {len(words_data)} weekly words")
    
    updated = 0
    created = 0
    errors = 0
    
    with db_manager.get_cursor() as cursor:
        for word_data in words_data:
            word = word_data['word'].strip()
            translation = word_data['translation'].strip()
            usage1 = word_data['usage1'].strip() if word_data.get('usage1') else ''
            usage2 = word_data['usage2'].strip() if word_data.get('usage2') else ''
            provenance = word_data['provenance'].strip() if word_data.get('provenance') else ''
            
            if not word:
                logger.warning("Skipping row with empty word")
                continue
            
            # Format description
            idea_description = format_description(translation, usage1, usage2, provenance)
            
            # Check if word already exists
            cursor.execute("""
                SELECT id FROM calendar_ideas
                WHERE item_classification = 'weekly_word'
                AND idea_title = %s
            """, (word,))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE calendar_ideas
                    SET idea_description = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (idea_description, existing['id']))
                updated += 1
                logger.info(f"Updated: {word} (ID: {existing['id']})")
            else:
                # Create new record (need to assign a week_number)
                # Find the highest week_number for weekly_word and add 1, or use 1 if none exist
                cursor.execute("""
                    SELECT COALESCE(MAX(week_number), 0) + 1 as next_week
                    FROM calendar_ideas
                    WHERE item_classification = 'weekly_word'
                """)
                result = cursor.fetchone()
                week_number = result['next_week'] if result else 1
                
                cursor.execute("""
                    INSERT INTO calendar_ideas (
                        week_number,
                        idea_title,
                        idea_description,
                        item_classification,
                        is_recurring
                    ) VALUES (%s, %s, %s, 'weekly_word', TRUE)
                """, (week_number, word, idea_description))
                created += 1
                logger.info(f"Created: {word} (week_number: {week_number})")
    
    logger.info(f"Update complete: {updated} updated, {created} created, {errors} errors")
    return {
        'updated': updated,
        'created': created,
        'errors': errors,
        'total': len(words_data)
    }


if __name__ == "__main__":
    try:
        stats = update_weekly_words()
        print(f"\n✅ Update complete!")
        print(f"   Updated: {stats['updated']}")
        print(f"   Created: {stats['created']}")
        print(f"   Total processed: {stats['total']}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error updating weekly words: {e}", exc_info=True)
        sys.exit(1)
