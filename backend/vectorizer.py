"""
Devpost Project Vectorizer
Creates high-dimensional vectors for hackathon projects based on multiple similarity dimensions.

Similar projects should have similar vectors based on:
- End user/target audience
- Use case/application domain
- Tech stack
- Medium/platform
- Problem domain
- Team composition
- Awards/recognition
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import re
from typing import Dict, List, Tuple, Any
import pickle
import os


class DevpostVectorizer:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        Initialize the vectorizer with a sentence transformer model.
        
        Args:
            model_name: HuggingFace model name for sentence embeddings
        """
        self.model_name = model_name
        self.sentence_model = SentenceTransformer(model_name)
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=50)
        
        # Category mappings for tech stacks, domains, etc.
        self.tech_categories = {
            'web': ['react', 'vue', 'angular', 'html', 'css', 'javascript', 'typescript', 'next.js', 'nuxt'],
            'mobile': ['ios', 'android', 'flutter', 'react native', 'swift', 'kotlin', 'xamarin'],
            'backend': ['python', 'node.js', 'express', 'django', 'flask', 'fastapi', 'spring', 'java'],
            'database': ['mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'supabase', 'firebase'],
            'ai_ml': ['tensorflow', 'pytorch', 'scikit-learn', 'opencv', 'numpy', 'pandas', 'machine learning', 'ai'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'heroku', 'vercel'],
            'blockchain': ['ethereum', 'solidity', 'web3', 'blockchain', 'crypto', 'defi', 'nft'],
            'iot': ['arduino', 'raspberry pi', 'esp32', 'sensors', 'iot', 'hardware'],
            'data': ['pandas', 'numpy', 'matplotlib', 'seaborn', 'jupyter', 'data analysis', 'visualization']
        }
        
        self.domain_categories = {
            'healthcare': ['health', 'medical', 'hospital', 'patient', 'doctor', 'medicine', 'fitness', 'wellness'],
            'education': ['education', 'learning', 'school', 'student', 'teacher', 'course', 'tutorial'],
            'finance': ['finance', 'banking', 'fintech', 'payment', 'money', 'investment', 'trading', 'crypto'],
            'social': ['social', 'community', 'chat', 'messaging', 'social media', 'networking'],
            'productivity': ['productivity', 'organization', 'task', 'management', 'workflow', 'collaboration'],
            'entertainment': ['game', 'music', 'video', 'entertainment', 'fun', 'leisure', 'media'],
            'environment': ['environment', 'climate', 'sustainability', 'green', 'renewable', 'carbon'],
            'accessibility': ['accessibility', 'disability', 'inclusive', 'assistive', 'inclusion'],
            'security': ['security', 'privacy', 'encryption', 'cybersecurity', 'safe', 'protection']
        }
        
        self.user_categories = {
            'consumers': ['consumer', 'user', 'customer', 'individual', 'personal', 'everyday'],
            'businesses': ['business', 'enterprise', 'company', 'corporate', 'professional', 'b2b'],
            'developers': ['developer', 'programmer', 'engineer', 'technical', 'coding', 'api'],
            'students': ['student', 'academic', 'university', 'college', 'learning', 'education'],
            'healthcare_professionals': ['doctor', 'nurse', 'medical', 'healthcare', 'clinical', 'patient'],
            'educators': ['teacher', 'instructor', 'educator', 'professor', 'academic', 'learning']
        }

    def extract_features(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured features from project data.
        
        Args:
            project_data: Dictionary containing scraped project data
            
        Returns:
            Dictionary of extracted features
        """
        features = {}
        
        # Basic project info
        features['title'] = project_data.get('title', '')
        features['tagline'] = project_data.get('tagline', '')
        features['hackathon'] = project_data.get('hackathon', '')
        
        # Combine all text content for analysis
        all_text = []
        if features['title']:
            all_text.append(features['title'])
        if features['tagline']:
            all_text.append(features['tagline'])
        
        # Add description sections
        if 'description' in project_data and project_data['description']:
            for section in project_data['description']:
                if isinstance(section, dict) and 'content' in section:
                    all_text.append(section['content'])
        
        features['combined_text'] = ' '.join(all_text)
        
        # Extract tech stack
        features['tech_stack'] = self._extract_tech_stack(project_data.get('built_with', []))
        
        # Extract team info
        features['team_size'] = len(project_data.get('team_members', []))
        features['team_names'] = [member.get('name', '') for member in project_data.get('team_members', [])]
        
        # Extract awards
        features['awards'] = project_data.get('awards', [])
        features['has_awards'] = len(features['awards']) > 0
        
        # Extract domain categories
        features['domains'] = self._extract_domains(features['combined_text'])
        features['target_users'] = self._extract_target_users(features['combined_text'])
        
        return features

    def _extract_tech_stack(self, built_with: List[str]) -> Dict[str, float]:
        """Extract tech stack categories and their weights."""
        tech_scores = {category: 0.0 for category in self.tech_categories.keys()}
        
        if not built_with:
            return tech_scores
        
        # Convert to lowercase for matching
        built_with_lower = [tech.lower() for tech in built_with]
        all_tech_text = ' '.join(built_with_lower)
        
        for category, keywords in self.tech_categories.items():
            for keyword in keywords:
                if keyword in all_tech_text:
                    tech_scores[category] += 1.0
        
        # Normalize scores
        total_score = sum(tech_scores.values())
        if total_score > 0:
            tech_scores = {k: v/total_score for k, v in tech_scores.items()}
        
        return tech_scores

    def _extract_domains(self, text: str) -> Dict[str, float]:
        """Extract domain categories from text."""
        domain_scores = {category: 0.0 for category in self.domain_categories.keys()}
        
        if not text:
            return domain_scores
        
        text_lower = text.lower()
        
        for category, keywords in self.domain_categories.items():
            for keyword in keywords:
                if keyword in text_lower:
                    domain_scores[category] += 1.0
        
        # Normalize scores
        total_score = sum(domain_scores.values())
        if total_score > 0:
            domain_scores = {k: v/total_score for k, v in domain_scores.items()}
        
        return domain_scores

    def _extract_target_users(self, text: str) -> Dict[str, float]:
        """Extract target user categories from text."""
        user_scores = {category: 0.0 for category in self.user_categories.keys()}
        
        if not text:
            return user_scores
        
        text_lower = text.lower()
        
        for category, keywords in self.user_categories.items():
            for keyword in keywords:
                if keyword in text_lower:
                    user_scores[category] += 1.0
        
        # Normalize scores
        total_score = sum(user_scores.values())
        if total_score > 0:
            user_scores = {k: v/total_score for k, v in user_scores.items()}
        
        return user_scores

    def create_semantic_embedding(self, text: str) -> np.ndarray:
        """Create semantic embedding using sentence transformer."""
        if not text:
            return np.zeros(self.sentence_model.get_sentence_embedding_dimension())
        
        return self.sentence_model.encode(text)

    def create_tech_embedding(self, tech_stack: Dict[str, float]) -> np.ndarray:
        """Create embedding for tech stack."""
        categories = list(self.tech_categories.keys())
        return np.array([tech_stack.get(cat, 0.0) for cat in categories])

    def create_domain_embedding(self, domains: Dict[str, float]) -> np.ndarray:
        """Create embedding for domain categories."""
        categories = list(self.domain_categories.keys())
        return np.array([domains.get(cat, 0.0) for cat in categories])

    def create_user_embedding(self, target_users: Dict[str, float]) -> np.ndarray:
        """Create embedding for target users."""
        categories = list(self.user_categories.keys())
        return np.array([target_users.get(cat, 0.0) for cat in categories])

    def create_award_embedding(self, awards: List[str]) -> np.ndarray:
        """Create a fixed-size embedding for awards using a hashing trick.

        We avoid per-document TF-IDF vocab (which yields variable-length vectors)
        and instead map tokens into a fixed-length bucketed vector.
        """
        HASH_DIM = 64
        vec = np.zeros(HASH_DIM, dtype=float)
        if not awards:
            return vec

        text = ' '.join(awards).lower()
        # Simple tokenization on non-alphanumerics
        tokens = re.split(r"[^a-z0-9_+-]+", text)
        for tok in tokens:
            if not tok:
                continue
            h = hash(tok)  # Python's hash is fine for a bucket index here
            idx = h % HASH_DIM
            vec[idx] += 1.0
        # L2 normalize for scale invariance
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def create_team_embedding(self, team_size: int, team_names: List[str]) -> np.ndarray:
        """Create embedding for team characteristics."""
        # Team size (normalized)
        size_embedding = np.array([team_size / 10.0])  # Normalize to 0-1
        
        # Team name diversity (simple heuristic)
        unique_names = len(set(team_names))
        diversity_embedding = np.array([unique_names / max(team_size, 1)])
        
        return np.concatenate([size_embedding, diversity_embedding])

    def vectorize_project(self, project_data: Dict[str, Any]) -> Dict[str, np.ndarray]:
        """
        Create comprehensive vector representation of a project.
        
        Args:
            project_data: Dictionary containing scraped project data
            
        Returns:
            Dictionary containing different types of embeddings
        """
        features = self.extract_features(project_data)
        
        vectors = {}
        
        # Semantic embeddings
        vectors['semantic'] = self.create_semantic_embedding(features['combined_text'])
        vectors['title_semantic'] = self.create_semantic_embedding(features['title'])
        vectors['tagline_semantic'] = self.create_semantic_embedding(features['tagline'])
        
        # Categorical embeddings
        vectors['tech_stack'] = self.create_tech_embedding(features['tech_stack'])
        vectors['domains'] = self.create_domain_embedding(features['domains'])
        vectors['target_users'] = self.create_user_embedding(features['target_users'])
        
        # Specialized embeddings
        vectors['awards'] = self.create_award_embedding(features['awards'])
        vectors['team'] = self.create_team_embedding(features['team_size'], features['team_names'])
        
        # Combined embedding
        vectors['combined'] = np.concatenate([
            vectors['semantic'],
            vectors['tech_stack'],
            vectors['domains'],
            vectors['target_users'],
            vectors['awards'],
            vectors['team']
        ])
        
        return vectors

    def create_similarity_matrix(self, projects: List[Dict[str, Any]], 
                               similarity_type: str = 'combined') -> np.ndarray:
        """
        Create similarity matrix between projects.
        
        Args:
            projects: List of project data dictionaries
            similarity_type: Type of embedding to use for similarity ('combined', 'semantic', etc.)
            
        Returns:
            NxN similarity matrix
        """
        vectors = []
        for project in projects:
            project_vectors = self.vectorize_project(project)
            vectors.append(project_vectors[similarity_type])
        
        vectors = np.array(vectors)
        
        # Normalize vectors
        vectors = self.scaler.fit_transform(vectors)
        
        # Compute cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        similarity_matrix = cosine_similarity(vectors)
        
        return similarity_matrix

    def find_similar_projects(self, target_project: Dict[str, Any], 
                            all_projects: List[Dict[str, Any]], 
                            top_k: int = 5,
                            similarity_type: str = 'combined') -> List[Tuple[Dict[str, Any], float]]:
        """
        Find most similar projects to target project.
        
        Args:
            target_project: Project to find similarities for
            all_projects: List of all projects to search in
            top_k: Number of similar projects to return
            similarity_type: Type of embedding to use
            
        Returns:
            List of tuples (project, similarity_score)
        """
        target_vector = self.vectorize_project(target_project)[similarity_type]
        
        similarities = []
        for project in all_projects:
            project_vector = self.vectorize_project(project)[similarity_type]
            
            # Compute cosine similarity
            similarity = np.dot(target_vector, project_vector) / (
                np.linalg.norm(target_vector) * np.linalg.norm(project_vector)
            )
            
            similarities.append((project, similarity))
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def save_model(self, filepath: str):
        """Save the vectorizer model and components."""
        model_data = {
            'model_name': self.model_name,
            'tech_categories': self.tech_categories,
            'domain_categories': self.domain_categories,
            'user_categories': self.user_categories,
            'scaler': self.scaler,
            'pca': self.pca
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

    def load_model(self, filepath: str):
        """Load the vectorizer model and components."""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model_name = model_data['model_name']
        self.sentence_model = SentenceTransformer(self.model_name)
        self.tech_categories = model_data['tech_categories']
        self.domain_categories = model_data['domain_categories']
        self.user_categories = model_data['user_categories']
        self.scaler = model_data['scaler']
        self.pca = model_data['pca']


def main():
    """Example usage of the vectorizer."""
    # Load sample project data
    with open('plate-o_scraped.json', 'r') as f:
        sample_project = json.load(f)
    
    # Initialize vectorizer
    vectorizer = DevpostVectorizer()
    
    # Vectorize the project
    vectors = vectorizer.vectorize_project(sample_project)
    
    print("Project vectors created:")
    for vector_type, vector in vectors.items():
        print(f"{vector_type}: shape {vector.shape}")
    
    # Save the model
    vectorizer.save_model('devpost_vectorizer.pkl')
    print("Model saved to devpost_vectorizer.pkl")


if __name__ == "__main__":
    main()
