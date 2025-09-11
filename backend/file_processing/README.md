
While it would be nice to use the file metadata for the "file owner" kind of
info, because we are using the volume mounts, it is really wasteful.

What we will do is create a path: "uploads/{user_id}/{filename}" and then pattern
match to retrieve the user id.
During processing, we want to save to the "results/{file_id}/{result_filename}".
There should be a METADATA file that is uploaded that has the path of the original
file.

But this is not enough, because the sender may want to share it with others...
Tho, really, we could make it such that the sender is the OWNER, and the file is
the RESOURCE that can be shared.

```ini
.
├── uploads
│   └── {user_id}
│       └── {filename}
└── results
        └── {file_id}
            ├── METADATA
            ├── index.html
            ├── sections.jsonl
            └── chunks
                ├── chunk0.json
                ├── chunk1.json
                └── ...
```

Then, if I want to know what file the user uploaded, I can look at the
uploads/{user_id}/ folder and just list the filenames.

During the file processing:

- Generate file_id
- Insert the KnowledgeSource instance to the database
- Create METADATA
- Create index.html
- Create sections.jsonl
- Create a chunks folder
- Split sections.jsonl into chunks

During the indexing (for each chunk):

- Read the chunk file
- Create the embedding of the:
  - Title
  - Text
  - Digest
- Insert the CHUNK instance to the database

CHUNK should be an embedding + chunk filename + chunk original file.




I have some task to be done with file processing. the issue is: I need to process the file (load the binary to memory, split it etc.) as well as query the REST API for metadata, get some properties and save it to database. Many of these operations are IO bound and I was hoping to interleave some of the operations, but how do i schedule the operations and not await them fully, a
