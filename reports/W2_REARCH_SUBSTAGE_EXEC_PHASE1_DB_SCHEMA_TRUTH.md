# W2 Re-architecture: DB Substage Registry Structural Truth (Report Only)

**Scope:** Verbatim DB structure and sample data for substage registry tables. No code changes. No refactors. No fixes.

---

## 1. Schema: substage_metadata

### `\d substage_metadata`

```
                                          Table "public.substage_metadata"
     Column     |            Type             | Collation | Nullable |                    Default                    
----------------+-----------------------------+-----------+----------+-----------------------------------------------
 id             | integer                     |           | not null | nextval('substage_metadata_id_seq'::regclass)
 substage_key   | character varying(100)      |           | not null | 
 label          | character varying(200)      |           | not null | 
 route_function | character varying(255)      |           |          | 
 display_order  | integer                     |           | not null | 999
 stage          | character varying(50)       |           | not null | 
 description    | text                        |           |          | 
 is_active      | boolean                     |           |          | true
 created_at     | timestamp without time zone |           |          | now()
 updated_at     | timestamp without time zone |           |          | now()
Indexes:
    "substage_metadata_pkey" PRIMARY KEY, btree (id)
    "idx_substage_metadata_active" btree (is_active)
    "idx_substage_metadata_stage" btree (stage)
    "idx_substage_metadata_stage_order" btree (stage, display_order)
    "unique_substage_key" UNIQUE CONSTRAINT, btree (substage_key)
Referenced by:
    TABLE "output_channel_substages" CONSTRAINT "fk_channel_substage_key" FOREIGN KEY (substage_key) REFERENCES substage_metadata(substage_key) ON DELETE RESTRICT
    TABLE "post_type_substages" CONSTRAINT "fk_substage_key" FOREIGN KEY (substage_key) REFERENCES substage_metadata(substage_key) ON DELETE RESTRICT
```

### information_schema.columns

```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'substage_metadata'
ORDER BY ordinal_position;
```

**Output:**

```
  column_name   |          data_type          | is_nullable |                column_default                 
----------------+-----------------------------+-------------+-----------------------------------------------
 id             | integer                     | NO          | nextval('substage_metadata_id_seq'::regclass)
 substage_key   | character varying           | NO          | 
 label          | character varying           | NO          | 
 route_function | character varying           | YES         | 
 display_order  | integer                     | NO          | 999
 stage          | character varying           | NO          | 
 description    | text                        | YES         | 
 is_active      | boolean                     | YES         | true
 created_at     | timestamp without time zone | YES         | now()
 updated_at     | timestamp without time zone | YES         | now()
(10 rows)
```

### Sample rows (ORDER BY id LIMIT 20)

```sql
SELECT * FROM substage_metadata ORDER BY id LIMIT 20;
```

**Output:**

```
 id |      substage_key       |          label           |                   route_function                    | display_order |   stage   | description | is_active |         created_at         |         updated_at         
----+-------------------------+--------------------------+-----------------------------------------------------+---------------+-----------+-------------+-----------+----------------------------+----------------------------
  1 | view                    | Calendar View            | planning.planning_calendar_view                     |             1 | calendar  |             | t         | 2025-12-16 17:01:46.106839 | 2025-12-16 17:01:56.266459
  2 | week-view               | Week View                | planning.planning_calendar_week_view                |             2 | calendar  |             | t         | 2025-12-16 17:01:46.107789 | 2025-12-16 17:01:56.268559
  3 | ideas-week              | Week Themes              |                                                     |             3 | calendar  |             | t         | 2025-12-16 17:01:46.107959 | 2025-12-16 17:01:56.269108
  4 | ideas                   | Ideas                    | planning.planning_calendar_ideas                    |             1 | planning  |             | t         | 2025-12-16 17:01:46.108093 | 2025-12-16 17:01:56.269679
  5 | taxonomy                | Taxonomy                 | planning.planning_calendar_taxonomy                 |             2 | planning  |             | t         | 2025-12-16 17:01:46.108252 | 2025-12-16 17:01:56.270079
  6 | topic_brainstorming     | Topic Brainstorming      | planning.planning_concept_brainstorm                |             3 | planning  |             | t         | 2025-12-16 17:01:46.108457 | 2025-12-16 17:01:56.270705
  7 | section_structure       | Section Structure Design | planning.planning_concept_section_structure         |             4 | planning  |             | t         | 2025-12-16 17:01:46.108567 | 2025-12-16 17:01:56.271088
  8 | topic_allocation        | Section Ideas            | planning.planning_concept_topic_allocation          |             5 | planning  |             | t         | 2025-12-16 17:01:46.108666 | 2025-12-16 17:01:56.271364
  9 | section_titling         | Section Titling          | planning.planning_concept_titling                   |             6 | planning  |             | t         | 2025-12-16 17:01:46.108768 | 2025-12-16 17:01:56.271633
 10 | product_data_review     | Product Data Review      | planning.planning_calendar_product_data_review      |             2 | planning  |             | t         | 2025-12-16 17:01:46.10887  | 2025-12-16 17:01:56.271913
 11 | section_content_mapping | Section Content Mapping  | planning.planning_concept_section_content_mapping   |             3 | planning  |             | t         | 2025-12-16 17:01:46.108964 | 2025-12-16 17:01:56.272155
 12 | research                | Research Overview        | planning.planning_research                          |             1 | research  |             | t         | 2025-12-16 17:01:46.109097 | 2025-12-16 17:01:56.272398
 13 | sources                 | Sources                  | planning.planning_research_sources                  |             2 | research  |             | t         | 2025-12-16 17:01:46.109194 | 2025-12-16 17:01:56.27261
 14 | visuals                 | Visuals                  | planning.planning_research_visuals                  |             3 | research  |             | t         | 2025-12-16 17:01:46.109339 | 2025-12-16 17:01:56.272882
 15 | prompts                 | Prompts                  | planning.planning_research_prompts                  |             4 | research  |             | t         | 2025-12-16 17:01:46.109469 | 2025-12-16 17:01:56.273163
 16 | verification            | Verification             | planning.planning_research_verification             |             5 | research  |             | t         | 2025-12-16 17:01:46.109569 | 2025-12-16 17:01:56.273496
 17 | drafting                | Drafting                 | authoring.authoring_sections_drafting               |             1 | authoring |             | t         | 2025-12-16 17:01:46.10968  | 2025-12-16 17:01:56.27371
 18 | image_concepts          | Image Concepts           | authoring_imaging.authoring_sections_image_concepts |             2 | authoring |             | t         | 2025-12-16 17:01:46.109875 | 2025-12-16 17:01:56.273912
 19 | image_prompts           | Image Prompts            | authoring_imaging.authoring_sections_image_prompts  |             3 | authoring |             | t         | 2025-12-16 17:01:46.110212 | 2025-12-16 17:01:56.274107
 20 | image_captions           | Image Captions           | authoring_imaging.authoring_sections_image_captions |             4 | authoring |             | t         | 2025-12-16 17:01:46.110301 | 2025-12-16 17:01:56.274291
(20 rows)
```

---

## 2. Schema: post_type_substages

### `\d post_type_substages`

```
                                          Table "public.post_type_substages"
    Column     |            Type             | Collation | Nullable |                     Default                     
---------------+-----------------------------+-----------+----------+-------------------------------------------------
 id            | integer                     |           | not null | nextval('post_type_substages_id_seq'::regclass)
 post_type     | character varying(50)       |           | not null | 
 stage         | character varying(50)       |           | not null | 
 substage_key  | character varying(100)      |           | not null | 
 display_order | integer                     |           | not null | 
 is_active     | boolean                     |           |          | true
 created_at    | timestamp without time zone |           |          | now()
 updated_at    | timestamp without time zone |           |          | now()
Indexes:
    "post_type_substages_pkey" PRIMARY KEY, btree (id)
    "idx_post_type_substages_active" btree (is_active)
    "idx_post_type_substages_lookup" btree (post_type, stage, is_active, display_order)
    "idx_post_type_substages_post_type" btree (post_type)
    "idx_post_type_substages_stage" btree (stage)
    "unique_post_type_stage_substage" UNIQUE CONSTRAINT, btree (post_type, stage, substage_key)
Foreign-key constraints:
    "fk_substage_key" FOREIGN KEY (substage_key) REFERENCES substage_metadata(substage_key) ON DELETE RESTRICT
```

### information_schema.columns

```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'post_type_substages'
ORDER BY ordinal_position;
```

**Output:**

```
  column_name  |          data_type          | is_nullable |                 column_default                  
---------------+-----------------------------+-------------+-------------------------------------------------
 id            | integer                     | NO          | nextval('post_type_substages_id_seq'::regclass)
 post_type     | character varying           | NO          | 
 stage         | character varying           | NO          | 
 substage_key  | character varying           | NO          | 
 display_order | integer                     | NO          | 
 is_active     | boolean                     | YES         | true
 created_at    | timestamp without time zone | YES         | now()
 updated_at    | timestamp without time zone | YES         | now()
(8 rows)
```

### Sample rows (ORDER BY id LIMIT 50)

```sql
SELECT * FROM post_type_substages ORDER BY id LIMIT 50;
```

**Output:**

```
 id | post_type |   stage   |      substage_key       | display_order | is_active |         created_at         |         updated_at         
----+-----------+-----------+-------------------------+---------------+-----------+----------------------------+----------------------------
  1 | themed    | calendar  | view                    |             1 | t         | 2025-12-16 17:01:46.111292 | 2025-12-16 17:01:56.276477
  2 | themed    | calendar  | week-view               |             2 | t         | 2025-12-16 17:01:46.111983 | 2025-12-16 17:01:56.277129
  3 | themed    | calendar  | ideas-week              |             3 | t         | 2025-12-16 17:01:46.11214  | 2025-12-16 17:01:56.277427
  4 | themed    | planning  | ideas                   |             1 | t         | 2025-12-16 17:01:46.112337 | 2025-12-16 17:01:56.277712
  5 | themed    | planning  | taxonomy                |             2 | t         | 2025-12-16 17:01:46.112503 | 2025-12-16 17:01:56.277973
  6 | themed    | planning  | topic_brainstorming     |             3 | t         | 2025-12-16 17:01:46.112695 | 2025-12-16 17:01:56.278355
  7 | themed    | planning  | section_structure       |             4 | t         | 2025-12-16 17:01:46.11283  | 2025-12-16 17:01:56.278602
  8 | themed    | planning  | topic_allocation        |             5 | t         | 2025-12-16 17:01:46.112947 | 2025-12-16 17:01:56.278816
  9 | themed    | planning  | section_titling         |             6 | t         | 2025-12-16 17:01:46.113096 | 2025-12-16 17:01:56.279045
 10 | themed    | research  | research                |             1 | t         | 2025-12-16 17:01:46.113205 | 2025-12-16 17:01:56.279238
 11 | themed    | research  | sources                 |             2 | t         | 2025-12-16 17:01:46.113325 | 2025-12-16 17:01:56.279421
 12 | themed    | research  | visuals                 |             3 | t         | 2025-12-16 17:01:46.113448 | 2025-12-16 17:01:56.279609
 13 | themed    | research  | prompts                 |             4 | t         | 2025-12-16 17:01:46.113536 | 2025-12-16 17:01:56.279773
 14 | themed    | research  | verification            |             5 | t         | 2025-12-16 17:01:46.113746 | 2025-12-16 17:01:56.279937
 15 | themed    | authoring | drafting                |             1 | t         | 2025-12-16 17:01:46.113931 | 2025-12-16 17:01:56.2801
 16 | themed    | authoring | image_concepts          |             2 | t         | 2025-12-16 17:01:46.114038 | 2025-12-16 17:01:56.280264
 17 | themed    | authoring | image_prompts           |             3 | t         | 2025-12-16 17:01:46.114122 | 2025-12-16 17:01:56.280436
 18 | themed    | authoring | image_captions          |             4 | t         | 2025-12-16 17:01:46.114209 | 2025-12-16 17:01:56.28061
 19 | themed    | imaging   | image_generation        |             1 | t         | 2025-12-16 17:01:46.114297 | 2025-12-16 17:01:56.280779
 20 | themed    | imaging   | optimise                |             2 | t         | 2025-12-16 17:01:46.114396 | 2025-12-16 17:01:56.280955
 21 | themed    | header    | title_summary           |             1 | t         | 2025-12-16 17:01:46.114483 | 2025-12-16 17:01:56.281495
 22 | themed    | header    | header_image            |             2 | t         | 2025-12-16 17:01:46.114567 | 2025-12-16 17:01:56.281671
 23 | themed    | header    | seo_meta                |             3 | t         | 2025-12-16 17:01:46.114659 | 2025-12-16 17:01:56.281852
 24 | themed    | header    | product_match           |             4 | t         | 2025-12-16 17:01:46.11474  | 2025-12-16 17:01:56.28207
 25 | themed    | header    | final_review            |             5 | t         | 2025-12-16 17:01:46.114879 | 2025-12-16 17:01:56.282244
 26 | profile   | planning  | taxonomy                |             1 | t         | 2025-12-16 17:01:46.115028 | 2025-12-16 17:01:56.282427
 27 | profile   | planning  | section_structure       |             2 | t         | 2025-12-16 17:01:46.115164 | 2025-12-16 17:01:56.282609
 28 | profile   | planning  | topic_allocation        |             3 | t         | 2025-12-16 17:01:46.115297 | 2025-12-16 17:01:56.28281
 29 | profile   | planning  | section_titling         |             4 | t         | 2025-12-16 17:01:46.115417 | 2025-12-16 17:01:56.283012
 30 | profile   | authoring | drafting                |             1 | t         | 2025-12-16 17:01:46.115511 | 2025-12-16 17:01:56.283224
 31 | profile   | authoring | image_concepts          |             2 | t         | 2025-12-16 17:01:46.11562  | 2025-12-16 17:01:56.283386
 32 | profile   | authoring | image_prompts           |             3 | t         | 2025-12-16 17:01:46.115736 | 2025-12-16 17:01:56.283484
 33 | profile   | authoring | image_captions          |             4 | t         | 2025-12-16 17:01:46.11583  | 2025-12-16 17:01:56.283587
 34 | profile   | imaging   | image_generation        |             1 | t         | 2025-12-16 17:01:46.115926 | 2025-12-16 17:01:56.283709
 35 | profile   | imaging   | optimise                |             2 | t         | 2025-12-16 17:01:46.116021 | 2025-12-16 17:01:56.283788
 36 | profile   | header    | title_summary           |             1 | t         | 2025-12-16 17:01:46.116105 | 2025-12-16 17:01:56.283863
 37 | profile   | header    | header_image            |             2 | t         | 2025-12-16 17:01:46.116194 | 2025-12-16 17:01:56.283941
 38 | profile   | header    | seo_meta                |             3 | t         | 2025-12-16 17:01:46.116353 | 2025-12-16 17:01:56.284127
 39 | profile   | header    | final_review            |             4 | t         | 2025-12-16 17:01:46.116442 | 2025-12-16 17:01:56.284228
 40 | generated | calendar  | view                    |             1 | t         | 2025-12-16 17:01:46.116529 | 2025-12-16 17:01:56.284311
 41 | generated | calendar  | week-view               |             2 | t         | 2025-12-16 17:01:46.116617 | 2025-12-16 17:01:56.284392
 42 | generated | calendar  | ideas-week              |             3 | t         | 2025-12-16 17:01:46.116706 | 2025-12-16 17:01:56.284482
 43 | generated | planning  | taxonomy                |             1 | t         | 2025-12-16 17:01:46.116795 | 2025-12-16 17:01:56.284568
 44 | generated | planning  | product_data_review     |             2 | t         | 2025-12-16 17:01:46.116886 | 2025-12-16 17:01:56.284645
 45 | generated | planning  | section_content_mapping |             3 | t         | 2025-12-16 17:01:46.11698  | 2025-12-16 17:01:56.284727
 46 | generated | planning  | section_titling         |             4 | t         | 2025-12-16 17:01:46.117057 | 2025-12-16 17:01:56.284829
 47 | generated | authoring | drafting                |             1 | t         | 2025-12-16 17:01:46.117144 | 2025-12-16 17:01:56.284961
 48 | generated | authoring | image_concepts          |             2 | t         | 2025-12-16 17:01:46.117229 | 2025-12-16 17:01:56.285066
 49 | generated | authoring | image_prompts           |             3 | t         | 2025-12-16 17:01:46.117314 | 2025-12-16 17:01:56.285143
 50 | generated | authoring | image_captions          |             4 | t         | 2025-12-16 17:01:46.1174   | 2025-12-16 17:01:56.285222
(50 rows)
```

---

## 3. Schema: output_channel_substages

### `\d output_channel_substages`

```
                                             Table "public.output_channel_substages"
        Column        |            Type             | Collation | Nullable |                       Default                        
----------------------+-----------------------------+-----------+----------+------------------------------------------------------
 id                   | integer                     |           | not null | nextval('output_channel_substages_id_seq'::regclass)
 post_type            | character varying(50)       |           | not null | 
 output_channel       | character varying(50)       |           | not null | 
 stage                | character varying(50)       |           | not null | 
 substage_key         | character varying(100)      |           | not null | 
 display_order        | integer                     |           | not null | 
 use_post_type_config | boolean                     |           |          | false
 is_active            | boolean                     |           |          | true
 created_at           | timestamp without time zone |           |          | now()
 updated_at           | timestamp without time zone |           |          | now()
Indexes:
    "output_channel_substages_pkey" PRIMARY KEY, btree (id)
    "idx_output_channel_substages_lookup" btree (post_type, output_channel, stage, is_active, display_order)
    "idx_output_channel_substages_post_type_channel" btree (post_type, output_channel)
    "unique_channel_substage" UNIQUE CONSTRAINT, btree (post_type, output_channel, stage, substage_key)
Foreign-key constraints:
    "fk_channel_substage_key" FOREIGN KEY (substage_key) REFERENCES substage_metadata(substage_key) ON DELETE RESTRICT
```

### information_schema.columns

```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'output_channel_substages'
ORDER BY ordinal_position;
```

**Output:**

```
     column_name      |          data_type          | is_nullable |                    column_default                    
----------------------+-----------------------------+-------------+------------------------------------------------------
 id                   | integer                     | NO          | nextval('output_channel_substages_id_seq'::regclass)
 post_type            | character varying           | NO          | 
 output_channel       | character varying           | NO          | 
 stage                | character varying           | NO          | 
 substage_key         | character varying           | NO          | 
 display_order        | integer                     | NO          | 
 use_post_type_config | boolean                     | YES         | false
 is_active            | boolean                     | YES         | true
 created_at           | timestamp without time zone | YES         | now()
 updated_at           | timestamp without time zone | YES         | now()
(10 rows)
```

### Sample rows (ORDER BY id LIMIT 50)

```sql
SELECT * FROM output_channel_substages ORDER BY id LIMIT 50;
```

**Output:**

```
 id |   post_type   | output_channel |    stage    |      substage_key      | display_order | use_post_type_config | is_active |         created_at         |         updated_at         
----+---------------+----------------+-------------+------------------------+---------------+----------------------+-----------+----------------------------+----------------------------
  1 | weekly_word   | facebook       | content     | format_for_facebook    |             1 | f                    | t         | 2025-12-16 17:01:46.120598 | 2025-12-16 17:01:56.288752
  2 | weekly_word   | facebook       | content     | add_hashtags           |             2 | f                    | t         | 2025-12-16 17:01:46.121314 | 2025-12-16 17:01:56.289152
  3 | weekly_word   | facebook       | imaging     | optimize_for_facebook  |             1 | f                    | t         | 2025-12-16 17:01:46.121829 | 2025-12-16 17:01:56.289344
  4 | weekly_word   | facebook       | publish     | publish_to_facebook    |             1 | f                    | t         | 2025-12-16 17:01:46.122152 | 2025-12-16 17:01:56.289547
  5 | weekly_phrase | facebook       | content     | format_for_facebook    |             1 | f                    | t         | 2025-12-16 17:01:46.122386 | 2025-12-16 17:01:56.289741
  6 | weekly_phrase | facebook       | content     | add_translation        |             2 | f                    | t         | 2025-12-16 17:01:46.122891 | 2025-12-16 17:01:56.290034
  7 | weekly_phrase | facebook       | content     | add_hashtags           |             3 | f                    | t         | 2025-12-16 17:01:46.123205 | 2025-12-16 17:01:56.290284
  8 | weekly_phrase | facebook       | imaging     | optimize_for_facebook  |             1 | f                    | t         | 2025-12-16 17:01:46.123382 | 2025-12-16 17:01:56.290463
  9 | weekly_phrase | facebook       | publish     | publish_to_facebook    |             1 | f                    | t         | 2025-12-16 17:01:46.123542 | 2025-12-16 17:01:56.290619
 10 | weekly_insult | facebook       | content     | format_for_facebook   |             1 | f                    | t         | 2025-12-16 17:01:46.123714 | 2025-12-16 17:01:56.290766
 11 | weekly_insult | facebook       | content     | add_translation        |             2 | f                    | t         | 2025-12-16 17:01:46.12388  | 2025-12-16 17:01:56.290906
 12 | weekly_insult | facebook       | content     | add_hashtags           |             3 | f                    | t         | 2025-12-16 17:01:46.124023 | 2025-12-16 17:01:56.291139
 13 | weekly_insult | facebook       | imaging     | optimize_for_facebook  |             1 | f                    | t         | 2025-12-16 17:01:46.124155 | 2025-12-16 17:01:56.291386
 14 | weekly_insult | facebook       | publish     | publish_to_facebook    |             1 | f                    | t         | 2025-12-16 17:01:46.12429  | 2025-12-16 17:01:56.291575
 15 | themed        | facebook       | syndication | extract_summary         |             1 | f                    | t         | 2025-12-16 17:01:46.124583 | 2025-12-16 17:01:56.291755
 16 | themed        | facebook       | syndication | format_for_facebook    |             2 | f                    | t         | 2025-12-16 17:01:46.124723 | 2025-12-16 17:01:56.291918
 17 | themed        | facebook       | syndication | publish_to_facebook    |             3 | f                    | t         | 2025-12-16 17:01:46.124916 | 2025-12-16 17:01:56.292069
 18 | recipe        | facebook       | syndication | extract_summary        |             1 | f                    | t         | 2025-12-16 17:01:46.125154 | 2025-12-16 17:01:56.292505
 19 | recipe        | facebook       | syndication | format_for_facebook   |             2 | f                    | t         | 2025-12-16 17:01:46.125322 | 2025-12-16 17:01:56.292659
 20 | recipe        | facebook       | syndication | publish_to_facebook    |             3 | f                    | t         | 2025-12-16 17:01:46.125481 | 2025-12-16 17:01:56.292793
 21 | profile       | facebook       | syndication | extract_summary        |             1 | f                    | t         | 2025-12-16 17:01:46.125641 | 2025-12-16 17:01:56.292935
 22 | profile       | facebook       | syndication | format_for_facebook    |             2 | f                    | t         | 2025-12-16 17:01:46.125797 | 2025-12-16 17:01:56.293071
 23 | profile       | facebook       | syndication | publish_to_facebook    |             3 | f                    | t         | 2025-12-16 17:01:46.125943 | 2025-12-16 17:01:56.293247
 24 | generated     | facebook       | syndication | extract_summary        |             1 | f                    | t         | 2025-12-16 17:01:46.126086 | 2025-12-16 17:01:56.293408
 25 | generated     | facebook       | syndication | format_for_facebook    |             2 | f                    | t         | 2025-12-16 17:01:46.126215 | 2025-12-16 17:01:56.293548
 26 | generated     | facebook       | syndication | publish_to_facebook    |             3 | f                    | t         | 2025-12-16 17:01:46.126506 | 2025-12-16 17:01:56.293682
 27 | weekly_word   | instagram      | content     | format_for_instagram   |             1 | f                    | t         | 2025-12-16 17:01:46.12673  | 2025-12-16 17:01:56.293851
 28 | weekly_word   | instagram      | content     | create_caption         |             2 | f                    | t         | 2025-12-16 17:01:46.126957 | 2025-12-16 17:01:56.29398
 29 | weekly_word   | instagram      | imaging     | optimize_for_instagram |             1 | f                    | t         | 2025-12-16 17:01:46.127179 | 2025-12-16 17:01:56.294111
 30 | weekly_word   | instagram      | imaging     | create_carousel        |             2 | f                    | t         | 2025-12-16 17:01:46.127406 | 2025-12-16 17:01:56.294244
 31 | weekly_word   | instagram      | publish     | publish_to_instagram   |             1 | f                    | t         | 2025-12-16 17:01:46.127632 | 2025-12-16 17:01:56.294381
 32 | weekly_phrase | instagram      | content     | format_for_instagram   |             1 | f                    | t         | 2025-12-16 17:01:46.127763 | 2025-12-16 17:01:56.294519
 33 | weekly_phrase | instagram      | content     | add_translation        |             2 | f                    | t         | 2025-12-16 17:01:46.127895 | 2025-12-16 17:01:56.294714
 34 | weekly_phrase | instagram      | content     | create_caption         |             3 | f                    | t         | 2025-12-16 17:01:46.12803  | 2025-12-16 17:01:56.294923
 35 | weekly_phrase | instagram      | imaging     | optimize_for_instagram |             1 | f                    | t         | 2025-12-16 17:01:46.128158 | 2025-12-16 17:01:56.295081
 36 | weekly_phrase | instagram      | imaging     | create_carousel        |             2 | f                    | t         | 2025-12-16 17:01:46.128293 | 2025-12-16 17:01:56.295246
 37 | weekly_phrase | instagram      | publish     | publish_to_instagram   |             1 | f                    | t         | 2025-12-16 17:01:46.12842  | 2025-12-16 17:01:56.295377
 38 | weekly_insult | instagram      | content     | format_for_instagram   |             1 | f                    | t         | 2025-12-16 17:01:46.128552 | 2025-12-16 17:01:56.295494
 39 | weekly_insult | instagram      | content     | add_translation        |             2 | f                    | t         | 2025-12-16 17:01:46.128682 | 2025-12-16 17:01:56.295617
 40 | weekly_insult | instagram      | content     | create_caption         |             3 | f                    | t         | 2025-12-16 17:01:46.128813 | 2025-12-16 17:01:56.295752
 41 | weekly_insult | instagram      | imaging     | optimize_for_instagram |             1 | f                    | t         | 2025-12-16 17:01:46.128942 | 2025-12-16 17:01:56.295893
 42 | weekly_insult | instagram      | imaging     | create_carousel        |             2 | f                    | t         | 2025-12-16 17:01:46.12909  | 2025-12-16 17:01:56.296074
 43 | weekly_insult | instagram      | publish     | publish_to_instagram   |             1 | f                    | t         | 2025-12-16 17:01:46.129225 | 2025-12-16 17:01:56.296265
 44 | themed        | instagram      | syndication | extract_summary         |             1 | f                    | t         | 2025-12-16 17:01:46.129361 | 2025-12-16 17:01:56.296409
 45 | themed        | instagram      | syndication | format_for_instagram   |             2 | f                    | t         | 2025-12-16 17:01:46.129486 | 2025-12-16 17:01:56.296546
 46 | themed        | instagram      | syndication | create_caption         |             3 | f                    | t         | 2025-12-16 17:01:46.129635 | 2025-12-16 17:01:56.296674
 47 | themed        | instagram      | syndication | publish_to_instagram   |             4 | f                    | t         | 2025-12-16 17:01:46.129775 | 2025-12-16 17:01:56.296874
 48 | recipe        | instagram      | syndication | extract_summary        |             1 | f                    | t         | 2025-12-16 17:01:46.129986 | 2025-12-16 17:01:56.297116
 49 | recipe        | instagram      | syndication | format_for_instagram   |             2 | f                    | t         | 2025-12-16 17:01:46.130132 | 2025-12-16 17:01:56.297311
 50 | recipe        | instagram      | syndication | create_caption         |             3 | f                    | t         | 2025-12-16 17:01:46.130269 | 2025-12-16 17:01:56.297484
(50 rows)
```

---

## 4. Constraints & Relationships

### substage_metadata

```sql
SELECT conname, pg_get_constraintdef(c.oid)
FROM pg_constraint c
JOIN pg_class t ON c.conrelid = t.oid
WHERE t.relname = 'substage_metadata';
```

**Output:**

```
        conname         | pg_get_constraintdef  
------------------------+-----------------------
 substage_metadata_pkey | PRIMARY KEY (id)
 unique_substage_key    | UNIQUE (substage_key)
(2 rows)
```

### post_type_substages

```sql
SELECT conname, pg_get_constraintdef(c.oid)
FROM pg_constraint c
JOIN pg_class t ON c.conrelid = t.oid
WHERE t.relname = 'post_type_substages';
```

**Output:**

```
             conname             |                                   pg_get_constraintdef                                   
---------------------------------+------------------------------------------------------------------------------------------
 fk_substage_key                 | FOREIGN KEY (substage_key) REFERENCES substage_metadata(substage_key) ON DELETE RESTRICT
 post_type_substages_pkey        | PRIMARY KEY (id)
 unique_post_type_stage_substage | UNIQUE (post_type, stage, substage_key)
(3 rows)
```

### output_channel_substages

```sql
SELECT conname, pg_get_constraintdef(c.oid)
FROM pg_constraint c
JOIN pg_class t ON c.conrelid = t.oid
WHERE t.relname = 'output_channel_substages';
```

**Output:**

```
            conname            |                                   pg_get_constraintdef                                   
-------------------------------+------------------------------------------------------------------------------------------
 fk_channel_substage_key       | FOREIGN KEY (substage_key) REFERENCES substage_metadata(substage_key) ON DELETE RESTRICT
 output_channel_substages_pkey | PRIMARY KEY (id)
 unique_channel_substage       | UNIQUE (post_type, output_channel, stage, substage_key)
(3 rows)
```

---

## 5. Stage Order Cross-Check

### Distinct stage in substage_metadata

```sql
SELECT DISTINCT stage FROM substage_metadata ORDER BY stage;
```

**Output:**

```
    stage    
-------------
 authoring
 calendar
 content
 header
 imaging
 planning
 publish
 research
 syndication
(9 rows)
```

### Distinct workflow_stage in post

```sql
SELECT DISTINCT workflow_stage FROM post ORDER BY workflow_stage;
```

**Output:**

```
 workflow_stage 
----------------
 metadata
 structure
(2 rows)
```

**Note:** `post.workflow_stage` check constraint allows: metadata, ideas, structure, titling, authoring, imaging, review. Current data only contains metadata and structure. Substage tables use stage names: authoring, calendar, content, header, imaging, planning, publish, research, syndication. There is no column named `workflow_stage` in the substage tables; alignment is by value (e.g. “planning” vs “ideas”/“structure”/“titling” in canonical early stages).

---

## 6. Does DB Contain Execution Logic?

```sql
SELECT column_name
FROM information_schema.columns
WHERE table_name IN ('substage_metadata','post_type_substages','output_channel_substages')
AND (column_name ILIKE '%function%'
   OR column_name ILIKE '%handler%'
   OR column_name ILIKE '%route%'
   OR column_name ILIKE '%min_stage%'
   OR column_name ILIKE '%order%'
   OR column_name ILIKE '%enabled%');
```

**Output:**

```
  column_name   
----------------
 display_order
 display_order
 display_order
 route_function
(4 rows)
```

So: **route_function** (substage_metadata only), **display_order** (all three tables). No **min_stage**, **handler**, or **enabled** column (is_active exists; “enabled” was the search term).

---

## 7. Rows for stage = 'ideas'

```sql
SELECT * FROM substage_metadata WHERE stage = 'ideas';
```

**Output:**

```
 id | substage_key | label | route_function | display_order | stage | description | is_active | created_at | updated_at 
----+--------------+-------+----------------+---------------+-------+-------------+-----------+------------+------------
(0 rows)
```

There are no rows with **stage** = 'ideas'. There is a row with **substage_key** = 'ideas' and **stage** = 'planning' (id 4).

---

## 8. Observed Structural Capabilities

- **Does DB contain min_stage?** No. No column named min_stage in any of the three tables.
- **Does DB contain execution order?** Partially. `display_order` exists in all three tables (order within stage). There is no global execution order across stages.
- **Does DB contain function/handler mapping?** Partially. `substage_metadata.route_function` holds a string (e.g. Flask route function name). No column for an execution handler or callable reference.
- **Does DB define post_type applicability?** Yes. `post_type_substages` has (post_type, stage, substage_key). `output_channel_substages` has (post_type, output_channel, stage, substage_key).
- **Does DB define default enabled/disabled?** Partially. `is_active` exists in all three tables (default true). No separate “default enabled for pipeline” vs “enabled for this post” in these tables.
- **Are stage names aligned with canonical stage names?** No. Substage tables use: authoring, calendar, content, header, imaging, planning, publish, research, syndication. Canonical `post.workflow_stage` uses: metadata, ideas, structure, titling, authoring, imaging, review. So “ideas” and “structure” and “titling” and “review” are workflow stages, not substage_metadata.stage values; “planning” is a stage in the substage tables but not a post.workflow_stage value.
- **Are there rows for stage = 'ideas'?** No. Zero rows in substage_metadata where stage = 'ideas'. The “ideas” concept appears as substage_key = 'ideas' under stage = 'planning'.

---

*End of report. No code changes. Commit only this file.*
