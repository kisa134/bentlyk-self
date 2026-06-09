import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple, Optional
import logging

class SemanticAlignmentLayer(nn.Module):
    def __init__(self, embedding_dim: int = 768, hidden_dim: int = 512):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        
        # Projection layers for Russian and English to shared space
        self.ru_projection = nn.Linear(embedding_dim, hidden_dim)
        self.en_projection = nn.Linear(embedding_dim, hidden_dim)
        
        # Alignment optimization components
        self.alignment_loss = nn.CosineEmbeddingLoss(margin=0.2)
        self.divergence_optimizer = torch.optim.Adam(self.parameters(), lr=1e-4)
        
        # State tracking
        self.active_language = "en"
        self.alignment_history = []
        self.cosine_similarities = []
        
        self.logger = logging.getLogger(__name__)
        
    def set_active_language(self, language: str) -> None:
        """Set the currently active language mode"""
        if language in ["ru", "en"]:
            self.active_language = language
            self.logger.debug(f"Active language set to: {language}")
        else:
            raise ValueError("Language must be 'ru' or 'en'")
            
    def project_semantic_frames(self, embeddings: torch.Tensor, language: str) -> torch.Tensor:
        """Project semantic embeddings into shared space based on language"""
        if language == "ru":
            return F.normalize(self.ru_projection(embeddings), dim=-1)
        elif language == "en":
            return F.normalize(self.en_projection(embeddings), dim=-1)
        else:
            raise ValueError("Language must be 'ru' or 'en'")
            
    def compute_cosine_similarity(self, ru_embeddings: torch.Tensor, 
                                en_embeddings: torch.Tensor) -> torch.Tensor:
        """Compute cosine similarity between projected embeddings"""
        # Normalize embeddings
        ru_norm = F.normalize(ru_embeddings, p=2, dim=-1)
        en_norm = F.normalize(en_embeddings, p=2, dim=-1)
        
        # Compute cosine similarity
        similarity = torch.sum(ru_norm * en_norm, dim=-1)
        return similarity
        
    def compute_divergence_loss(self, ru_projected: torch.Tensor, 
                              en_projected: torch.Tensor) -> torch.Tensor:
        """Compute loss to minimize divergence between equivalent concepts"""
        # Create target tensor (1 for similar, -1 for dissimilar)
        targets = torch.ones(ru_projected.size(0), device=ru_projected.device)
        
        # Compute cosine embedding loss
        loss = self.alignment_loss(ru_projected, en_projected, targets)
        return loss
        
    def optimize_alignment(self, ru_embeddings: torch.Tensor, 
                          en_embeddings: torch.Tensor) -> float:
        """Optimize alignment between semantic embeddings"""
        self.divergence_optimizer.zero_grad()
        
        # Project to shared space
        ru_projected = self.project_semantic_frames(ru_embeddings, "ru")
        en_projected = self.project_semantic_frames(en_embeddings, "en")
        
        # Compute loss and optimize
        loss = self.compute_divergence_loss(ru_projected, en_projected)
        loss.backward()
        self.divergence_optimizer.step()
        
        # Track metrics
        similarity = self.compute_cosine_similarity(ru_projected.detach(), en_projected.detach())
        self.alignment_history.append(loss.item())
        self.cosine_similarities.append(similarity.mean().item())
        
        return loss.item()
        
    def get_realtime_feedback(self) -> Dict[str, float]:
        """Provide real-time alignment feedback"""
        if not self.cosine_similarities:
            return {"alignment_score": 0.0, "divergence_loss": 0.0}
            
        recent_similarities = self.cosine_similarities[-10:]  # Last 10 measurements
        recent_losses = self.alignment_history[-10:] if self.alignment_history else [0.0]
        
        return {
            "alignment_score": float(np.mean(recent_similarities)),
            "divergence_loss": float(np.mean(recent_losses)),
            "language_mode": self.active_language
        }
        
    def forward(self, ru_embeddings: torch.Tensor, 
                en_embeddings: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass through semantic alignment layer"""
        # Project embeddings to shared space
        ru_projected = self.project_semantic_frames(ru_embeddings, "ru")
        en_projected = self.project_semantic_frames(en_embeddings, "en")
        
        # Optimize alignment in real-time
        self.optimize_alignment(ru_embeddings, en_embeddings)
        
        return ru_projected, en_projected

# Example usage:
# alignment_layer = SemanticAlignmentLayer()
# ru_emb = torch.randn(32, 768)  # Batch of 32 Russian embeddings
# en_emb = torch.randn(32, 768)  # Batch of 32 English embeddings
# ru_aligned, en_aligned = alignment_layer(ru_emb, en_emb)
# feedback = alignment_layer.get_realtime_feedback()