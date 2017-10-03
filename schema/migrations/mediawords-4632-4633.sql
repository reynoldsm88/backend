--
-- This is a Media Cloud PostgreSQL schema difference file (a "diff") between schema
-- versions 4632 and 4633.
--
-- If you are running Media Cloud with a database that was set up with a schema version
-- 4632, and you would like to upgrade both the Media Cloud and the
-- database to be at version 4633, import this SQL file:
--
--     psql mediacloud < mediawords-4632-4633.sql
--
-- You might need to import some additional schema diff files to reach the desired version.
--

--
-- 1 of 2. Import the output of 'apgdiff':
--

SET search_path = public, pg_catalog;


--
-- Returns true if the story can + should be annotated with NYTLabels
--
CREATE OR REPLACE FUNCTION story_is_annotatable_with_nytlabels(nytlabels_stories_id INT)
RETURNS boolean AS $$
DECLARE
    story record;
BEGIN

    SELECT stories_id, media_id, language INTO story from stories where stories_id = nytlabels_stories_id;

    IF NOT ( story.language = 'en' or story.language is null ) THEN
        RETURN FALSE;

    ELSEIF NOT EXISTS ( SELECT 1 FROM story_sentences WHERE stories_id = nytlabels_stories_id ) THEN
        RETURN FALSE;

    END IF;

    RETURN TRUE;

END;
$$
LANGUAGE 'plpgsql';


--
-- NYTLabels annotations
--
CREATE TABLE nytlabels_annotations (
    nytlabels_annotations_id  SERIAL    PRIMARY KEY,
    object_id                 INTEGER   NOT NULL REFERENCES stories (stories_id) ON DELETE CASCADE,
    raw_data                  BYTEA     NOT NULL
);
CREATE UNIQUE INDEX nytlabels_annotations_object_id ON nytlabels_annotations (object_id);

-- Don't (attempt to) compress BLOBs in "raw_data" because they're going to be
-- compressed already
ALTER TABLE nytlabels_annotations
    ALTER COLUMN raw_data SET STORAGE EXTERNAL;


CREATE OR REPLACE FUNCTION set_database_schema_version() RETURNS boolean AS $$
DECLARE
    -- Database schema version number (same as a SVN revision number)
    -- Increase it by 1 if you make major database schema changes.
    MEDIACLOUD_DATABASE_SCHEMA_VERSION CONSTANT INT := 4633;

BEGIN

    -- Update / set database schema version
    DELETE FROM database_variables WHERE name = 'database-schema-version';
    INSERT INTO database_variables (name, value) VALUES ('database-schema-version', MEDIACLOUD_DATABASE_SCHEMA_VERSION::int);

    return true;

END;
$$
LANGUAGE 'plpgsql';

--
-- 2 of 2. Reset the database version.
--
SELECT set_database_schema_version();

