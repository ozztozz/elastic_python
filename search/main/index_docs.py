import os
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, DATETIME
from whoosh.analysis import StandardAnalyzer, NgramWordAnalyzer

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs')
INDEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'whoosh_index')

schema = Schema(
    filename=ID(stored=True, unique=True),
    # Use StandardAnalyzer for better phrase/proximity support
    content=TEXT(stored=True, analyzer=StandardAnalyzer()),
    date=DATETIME(stored=True)
)

def create_or_open_index(force_reindex=False):
    if force_reindex and os.path.exists(INDEX_DIR):
        import shutil
        shutil.rmtree(INDEX_DIR)
    if not os.path.exists(INDEX_DIR):
        os.mkdir(INDEX_DIR)
        return index.create_in(INDEX_DIR, schema)
    else:
        return index.open_dir(INDEX_DIR)

def index_documents(force_reindex=False):
    ix = create_or_open_index(force_reindex=force_reindex)
    writer = ix.writer()
    import datetime
    for fname in os.listdir(DOCS_DIR):
        fpath = os.path.join(DOCS_DIR, fname)
        if os.path.isfile(fpath) and fname.endswith('.txt'):
            with open(fpath, encoding='utf-8') as f:
                content = f.read()
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fpath))
            # Debug: print tokens for this document
            print(f"Tokens for {fname}:")
            for token in StandardAnalyzer()(content):
                print(token.text, end=' ')
            print('\n---')
            writer.update_document(filename=fname, content=content, date=mtime)
            print(f"Indexed: {fname} ({mtime})")
    writer.commit()

if __name__ == '__main__':
    # Force reindex all documents every run
    index_documents(force_reindex=True)
