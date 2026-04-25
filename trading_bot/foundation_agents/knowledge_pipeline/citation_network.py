"""
Citation Network - Research Influence Tracking
=================================================

Tracks and analyzes citation networks to understand:
1. Research influence and impact
2. Knowledge flow patterns
3. Key papers and authors
4. Emerging research trends
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict
import networkx as nx

logger = logging.getLogger(__name__)


@dataclass
class PaperNode:
    """A paper in the citation network"""
    paper_id: str
    title: str
    authors: List[str] = field(default_factory=list)
    publication_year: Optional[int] = None
    
    # Citations
    citations_out: List[str] = field(default_factory=list)  # Papers this paper cites
    citations_in: List[str] = field(default_factory=list)  # Papers citing this paper
    
    # Metrics
    citation_count: int = 0
    reference_count: int = 0
    
    # Analysis
    influence_score: float = 0.0
    centrality: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'paper_id': self.paper_id,
            'title': self.title[:50] + "..." if len(self.title) > 50 else self.title,
            'authors': self.authors[:3],
            'year': self.publication_year,
            'citations': self.citation_count,
            'influence_score': self.influence_score
        }


@dataclass
class AuthorNode:
    """An author in the citation network"""
    author_id: str
    name: str
    
    # Papers
    papers: List[str] = field(default_factory=list)
    
    # Metrics
    total_citations: int = 0
    h_index: int = 0
    
    # Collaborations
    co_authors: Set[str] = field(default_factory=set)
    
    # Influence
    field_influence: float = 0.0


class CitationNetwork:
    """
    Citation Network
    
    Manages a graph of papers and their citation relationships,
    providing influence metrics and trend analysis.
    """
    
    def __init__(self):
        # Graph
        self.graph = nx.DiGraph()
        
        # Paper nodes
        self.papers: Dict[str, PaperNode] = {}
        self.authors: Dict[str, AuthorNode] = {}
        
        # Index by year
        self.papers_by_year: Dict[int, List[str]] = defaultdict(list)
        
        # Metrics cache
        self.influence_scores: Dict[str, float] = {}
        self.last_calculated: Optional[datetime] = None
        
        # Statistics
        self.stats = {
            'papers_added': 0,
            'citations_added': 0,
            'authors_added': 0
        }
        
        logger.info("Citation Network initialized")
    
    def add_paper(
        self,
        paper_id: str,
        title: str,
        authors: List[str],
        publication_year: Optional[int] = None,
        references: Optional[List[str]] = None
    ) -> PaperNode:
        """Add a paper to the network"""
        # Create or update paper node
        if paper_id in self.papers:
            paper = self.papers[paper_id]
        else:
            paper = PaperNode(
                paper_id=paper_id,
                title=title,
                authors=authors,
                publication_year=publication_year
            )
            self.papers[paper_id] = paper
            self.stats['papers_added'] += 1
        
        # Add to graph
        self.graph.add_node(paper_id, **{
            'title': title,
            'year': publication_year,
            'type': 'paper'
        })
        
        # Index by year
        if publication_year:
            self.papers_by_year[publication_year].append(paper_id)
        
        # Add authors
        for author_name in authors:
            author_id = self._get_author_id(author_name)
            if author_id not in self.authors:
                self.authors[author_id] = AuthorNode(
                    author_id=author_id,
                    name=author_name
                )
                self.stats['authors_added'] += 1
            
            if paper_id not in self.authors[author_id].papers:
                self.authors[author_id].papers.append(paper_id)
        
        # Add citations (references this paper makes)
        if references:
            for ref_id in references:
                self.add_citation(paper_id, ref_id)
        
        return paper
    
    def add_citation(self, from_paper: str, to_paper: str):
        """Add a citation relationship"""
        # Add edge
        self.graph.add_edge(from_paper, to_paper, type='cites')
        
        # Update paper nodes
        if from_paper in self.papers and to_paper not in self.papers[from_paper].citations_out:
            self.papers[from_paper].citations_out.append(to_paper)
            self.papers[from_paper].reference_count += 1
        
        if to_paper in self.papers and from_paper not in self.papers[to_paper].citations_in:
            self.papers[to_paper].citations_in.append(from_paper)
            self.papers[to_paper].citation_count += 1
        
        self.stats['citations_added'] += 1
    
    def _get_author_id(self, name: str) -> str:
        """Generate author ID from name"""
        return name.lower().replace(" ", "_")
    
    def calculate_influence_scores(self):
        """Calculate influence scores for all papers"""
        if not self.papers:
            return
        
        # Use PageRank as influence metric
        try:
            pagerank = nx.pagerank(self.graph, alpha=0.85)
            
            for paper_id, score in pagerank.items():
                if paper_id in self.papers:
                    self.papers[paper_id].influence_score = score
                    self.influence_scores[paper_id] = score
        except:
            # Fallback to simple citation count
            for paper_id, paper in self.papers.items():
                paper.influence_score = paper.citation_count / max(1, len(self.papers))
                self.influence_scores[paper_id] = paper.influence_score
        
        # Calculate centrality
        try:
            centrality = nx.degree_centrality(self.graph)
            for paper_id, cent in centrality.items():
                if paper_id in self.papers:
                    self.papers[paper_id].centrality = cent
        except:
            pass
        
        # Calculate author influence
        for author_id, author in self.authors.items():
            author_citations = sum(
                self.papers[pid].citation_count
                for pid in author.papers
                if pid in self.papers
            )
            author.total_citations = author_citations
            
            # Calculate h-index approximation
            paper_citations = sorted([
                self.papers[pid].citation_count
                for pid in author.papers
                if pid in self.papers
            ], reverse=True)
            
            h_index = 0
            for i, c in enumerate(paper_citations, 1):
                if c >= i:
                    h_index = i
                else:
                    break
            
            author.h_index = h_index
            author.field_influence = author_citations / max(1, len(author.papers))
        
        self.last_calculated = datetime.utcnow()
    
    def get_most_influential(
        self,
        n: int = 10,
        since_year: Optional[int] = None
    ) -> List[PaperNode]:
        """Get most influential papers"""
        if not self.influence_scores or not self.last_calculated:
            self.calculate_influence_scores()
        
        papers = list(self.papers.values())
        
        if since_year:
            papers = [p for p in papers if p.publication_year and p.publication_year >= since_year]
        
        papers.sort(key=lambda p: p.influence_score, reverse=True)
        
        return papers[:n]
    
    def get_most_influential_authors(self, n: int = 10) -> List[AuthorNode]:
        """Get most influential authors"""
        if not self.last_calculated:
            self.calculate_influence_scores()
        
        authors = list(self.authors.values())
        authors.sort(key=lambda a: a.field_influence, reverse=True)
        
        return authors[:n]
    
    def get_paper_network(
        self,
        paper_id: str,
        depth: int = 1
    ) -> Dict[str, Any]:
        """Get network around a specific paper"""
        if paper_id not in self.papers:
            return {}
        
        # BFS to get papers within depth
        visited = {paper_id}
        queue = [(paper_id, 0)]
        
        while queue:
            current, dist = queue.pop(0)
            
            if dist >= depth:
                continue
            
            # Get neighbors (both citations and references)
            neighbors = set()
            if current in self.papers:
                neighbors.update(self.papers[current].citations_out)
                neighbors.update(self.papers[current].citations_in)
            
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))
        
        return {
            'center_paper': paper_id,
            'network_size': len(visited) - 1,
            'papers': [self.papers[pid].to_dict() for pid in visited if pid in self.papers and pid != paper_id]
        }
    
    def find_emerging_research(self, years: int = 2) -> List[PaperNode]:
        """Find emerging high-impact research"""
        current_year = datetime.utcnow().year
        recent_year = current_year - years
        
        recent_papers = [
            p for p in self.papers.values()
            if p.publication_year and p.publication_year >= recent_year
        ]
        
        # Score by citation velocity (citations per year)
        for paper in recent_papers:
            years_since_pub = max(1, current_year - paper.publication_year)
            paper.influence_score = paper.citation_count / years_since_pub
        
        recent_papers.sort(key=lambda p: p.influence_score, reverse=True)
        
        return recent_papers[:10]
    
    def detect_research_clusters(self) -> List[Dict]:
        """Detect clusters of related research"""
        try:
            # Use community detection
            import networkx.algorithms.community as nx_comm
            
            # Convert to undirected for community detection
            undirected = self.graph.to_undirected()
            
            communities = nx_comm.greedy_modularity_communities(undirected)
            
            clusters = []
            for i, community in enumerate(communities):
                papers_in_community = [pid for pid in community if pid in self.papers]
                
                if len(papers_in_community) < 3:
                    continue
                
                # Find common keywords/themes
                keywords = defaultdict(int)
                for pid in papers_in_community:
                    paper = self.papers[pid]
                    # In production, extract actual keywords from papers
                    keywords[paper.title.split()[0]] += 1
                
                top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:3]
                
                clusters.append({
                    'cluster_id': i,
                    'size': len(papers_in_community),
                    'theme': ', '.join([k[0] for k in top_keywords]),
                    'avg_influence': np.mean([self.papers[pid].influence_score for pid in papers_in_community]),
                    'representative_papers': papers_in_community[:3]
                })
            
            return clusters
        except Exception as e:
            logger.error(f"Error detecting clusters: {e}")
            return []
    
    def get_citation_flow(
        self,
        from_year: int,
        to_year: int
    ) -> Dict[str, List[str]]:
        """Get citation flow between years"""
        flow = defaultdict(list)
        
        for paper_id, paper in self.papers.items():
            if not paper.publication_year:
                continue
            
            # Papers published in from_year citing papers in to_year
            if paper.publication_year == from_year:
                for ref in paper.citations_out:
                    if ref in self.papers:
                        ref_paper = self.papers[ref]
                        if ref_paper.publication_year == to_year:
                            flow[paper_id].append(ref)
        
        return dict(flow)
    
    def get_research_timeline(self, topic_keywords: List[str]) -> List[Dict]:
        """Get timeline of research on a topic"""
        relevant_papers = []
        
        for paper_id, paper in self.papers.items():
            # Check if paper matches topic
            text = (paper.title + " " + " ".join(paper.authors)).lower()
            if any(kw in text for kw in topic_keywords):
                relevant_papers.append(paper)
        
        # Sort by year
        relevant_papers.sort(key=lambda p: p.publication_year or 0)
        
        timeline = []
        for paper in relevant_papers:
            timeline.append({
                'year': paper.publication_year,
                'paper_id': paper.paper_id,
                'title': paper.title,
                'authors': paper.authors,
                'citations': paper.citation_count,
                'influence': paper.influence_score
            })
        
        return timeline
    
    def export_network_data(self) -> Dict:
        """Export network data for visualization"""
        return {
            'nodes': [
                {
                    'id': pid,
                    'label': paper.title[:30],
                    'year': paper.publication_year,
                    'citations': paper.citation_count,
                    'influence': paper.influence_score
                }
                for pid, paper in self.papers.items()
            ],
            'edges': [
                {
                    'source': from_paper,
                    'target': to_paper
                }
                for from_paper, to_paper in self.graph.edges()
            ]
        }
    
    def get_statistics(self) -> Dict:
        """Get network statistics"""
        return {
            **self.stats,
            'total_papers': len(self.papers),
            'total_authors': len(self.authors),
            'total_citations': self.stats['citations_added'],
            'density': nx.density(self.graph) if self.papers else 0,
            'connected_components': nx.number_weakly_connected_components(self.graph) if self.papers else 0
        }
