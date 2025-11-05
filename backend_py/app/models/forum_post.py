"""Forum Post Model - Community discussions, questions, announcements, and polls."""

from datetime import datetime
from typing import List, Optional, Literal
from beanie import Document, PydanticObjectId
from pydantic import Field
from bson import ObjectId


class Comment(Document):
    """Embedded comment schema for forum posts."""
    
    userId: PydanticObjectId = Field(...)
    content: str = Field(...)
    likes: List[PydanticObjectId] = Field(default_factory=list)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "comments"
        use_state_management = True


class PollOption(Document):
    """Poll option with votes."""
    
    text: str = Field(...)
    votes: List[PydanticObjectId] = Field(default_factory=list)


class ForumPost(Document):
    """Forum Post model for community discussions."""
    
    title: str = Field(...)
    content: str = Field(...)
    author: PydanticObjectId = Field(...)
    messId: Optional[PydanticObjectId] = None
    type: Literal['general', 'question', 'announcement', 'poll'] = Field(default='general')
    tags: List[str] = Field(default_factory=list)
    likes: List[PydanticObjectId] = Field(default_factory=list)
    comments: List[dict] = Field(default_factory=list)  # Store as dicts with _id
    pollOptions: Optional[List[dict]] = None  # Store as dicts
    isPollActive: bool = Field(default=True)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "forumposts"
        use_state_management = True
    
    def to_dict(self) -> dict:
        """Convert to dictionary with _id field."""
        data = {
            "_id": str(self.id),
            "title": self.title,
            "content": self.content,
            "author": str(self.author),
            "type": self.type,
            "tags": self.tags,
            "likes": [str(like) for like in self.likes],
            "comments": self.comments,
            "isPollActive": self.isPollActive,
            "createdAt": self.createdAt.isoformat() if self.createdAt else None,
            "updatedAt": self.updatedAt.isoformat() if self.updatedAt else None,
        }
        
        if self.messId:
            data["messId"] = str(self.messId)
        
        if self.pollOptions:
            data["pollOptions"] = self.pollOptions
        
        return data
