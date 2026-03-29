from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

from whoosh import index
from whoosh.qparser import MultifieldParser, OrGroup, PhrasePlugin, SequencePlugin
from whoosh import scoring
import re
import os

INDEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'whoosh_index')

def search_view(request: HttpRequest) -> HttpResponse:
	query = request.GET.get('q', '')
	results = []
	fulltexts = {}
	if query:
		# Build a phrase/proximity query and boost recency
		if os.path.exists(INDEX_DIR):
			ix = index.open_dir(INDEX_DIR)
			with ix.searcher(weighting=scoring.BM25F()) as searcher:
				parser = MultifieldParser(["content", "filename"], schema=ix.schema, group=OrGroup)
				parser.add_plugin(PhrasePlugin())
				parser.add_plugin(SequencePlugin())
				query_terms = [term for term in query.split() if term]
				
				def highlight_terms(text, terms):
					# Highlight all query terms in the text (case-insensitive)
					def repl(match):
						return f"<mark>{match.group(0)}</mark>"
					for term in sorted(terms, key=len, reverse=True):
						if term:
							pattern = re.compile(re.escape(term), re.IGNORECASE)
							text = pattern.sub(repl, text)
					return text

				hits = []
				used_docids = set()
				proximity_bonus = 1000  # Large enough to always rank above AND/OR
				proximity_scores = {}
				found = False
				# 1. Exact match (phrase, no slop, whole words)
				if ' ' in query.strip():
					# Add word boundaries to force whole word match
					words = query.strip().split()
					exact_phrase = ' '.join([f"{w}" for w in words])
					# Whoosh phrase queries already match whole words if analyzer is StandardAnalyzer
					exact_query = f'"{exact_phrase}"'
					print(f"Exact match query: {exact_query}")
					q_exact = parser.parse(exact_query)
					hits_exact = searcher.search(q_exact, limit=20, sortedby="date", reverse=True)
					print(f"Exact hits: {len(hits_exact)}")
					if hits_exact:
						for hit in hits_exact:
							hits.append(hit)
							used_docids.add(hit.docnum)
							proximity_scores[hit.docnum] = (hit.score + 2 * proximity_bonus, 'exact')
						found = True
				# 2. Proximity match (if no exact)
				if not found and ' ' in query.strip():
					phrase_query = f'"{query}"~30'  # within 30 words
					print(f"Proximity query: {phrase_query}")
					q_phrase = parser.parse(phrase_query)
					hits_phrase = searcher.search(q_phrase, limit=20, sortedby="date", reverse=True)
					print(f"Proximity hits: {len(hits_phrase)}")
					if hits_phrase:
						for hit in hits_phrase:
							hits.append(hit)
							used_docids.add(hit.docnum)
							proximity_scores[hit.docnum] = (hit.score + proximity_bonus, 'proximity')
						found = True
				# 3. AND/OR match (if no proximity or exact)
				if not found:
					q_and = parser.parse(query)
					hits_and = searcher.search(q_and, limit=20, sortedby="date", reverse=True)
					print(f"AND/OR hits: {len(hits_and)}")
					for hit in hits_and:
						hits.append(hit)
						used_docids.add(hit.docnum)
						proximity_scores[hit.docnum] = (hit.score, 'andor')

				# Collect all relevant sentences from all hits with scoring
				all_sentences = []
				phrase = ' '.join([f"{w}" for w in query.strip().split()])
				for hit in hits:
					content = hit['content']
					# Improved regex: split on sentence-ending punctuation, multiple newlines, or lines starting with a letter and parenthesis (e.g., a), b), etc.)
					sentences = re.split(r'(?<=[.!?])\s+|(?<=\n)(?=[a-zA-Z]\))|\n{2,}', content)
					score_type = proximity_scores.get(hit.docnum, (hit.score, 'andor'))
					doc_score, match_type = score_type
					for s in sentences:
						s_lower = s.lower()
						# Score: 3 = exact phrase, 2 = all words, 1 = any word, 0 = none
						if phrase and phrase.lower() in s_lower:
							sent_score = 3
						elif all(qt.lower() in s_lower for qt in query_terms):
							sent_score = 2
						elif any(qt.lower() in s_lower for qt in query_terms):
							sent_score = 1
						else:
							continue  # skip sentences with no match
						all_sentences.append({
							'sentence': s,
							'highlighted': highlight_terms(s, query_terms),
							'filename': hit['filename'],
							'doc_score': doc_score,
							'sent_score': sent_score,
							'match_type': match_type
						})
					# Load full text for this file and highlight query terms, and split into sentences for modal markup
					docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs')
					file_path = os.path.join(docs_dir, hit['filename'])
					try:
						with open(file_path, encoding='utf-8') as f:
							raw_text = f.read()
							doc_sentences = re.split(r'(?<=[.!?])\s+|(?<=\n)(?=[a-zA-Z]\))|\n{2,}', raw_text)
							fulltexts[hit['filename']] = {
								'sentences': doc_sentences,
								'highlighted': highlight_terms(raw_text, query_terms)
							}
					except Exception:
						fulltexts[hit['filename']] = {'sentences': [], 'highlighted': ''}

				# Sort all sentences by (sent_score, doc_score) descending
				all_sentences.sort(key=lambda x: (x['sent_score'], x['doc_score']), reverse=True)
				# Take top 20
				top_sentences = all_sentences[:20]
				# Prepare results for rendering
				results = []
				for sent in top_sentences:
					results.append({
						'filename': sent['filename'],
						'snippet': sent['highlighted'],
						'snippet_list': None,
						'score': round(sent['doc_score'], 2) if sent['doc_score'] is not None else None,
						'match_type': sent['match_type']
					})
	return render(request, 'main/search.html', {'query': query, 'results': results, 'fulltexts': fulltexts})
