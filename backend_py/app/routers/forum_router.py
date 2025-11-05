"""Forum Router - Community forum endpoints for discussions, polls, and Q&A."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Literal
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime
import math

from ..models.forum_post import ForumPost
from ..models.user import User
from ..models.mess import Mess

router = APIRouter(prefix="/api/forum", tags=["Forum"])


# Request Models
class CreatePostRequest(BaseModel):
    title: str
    content: str
    type: Literal['general', 'question', 'announcement', 'poll'] = 'general'
    messId: Optional[str] = None
    pollOptions: Optional[List[str]] = None


class UpdatePostRequest(BaseModel):
    title: str
    content: str
    type: Literal['general', 'question', 'announcement', 'poll']
    pollOptions: Optional[List[str]] = None


class AddCommentRequest(BaseModel):
    content: str


class VotePollRequest(BaseModel):
    optionIndex: int


# Create post
@router.post("/posts/create/{user_id}")
async def create_post(user_id: str, payload: CreatePostRequest):
    """Create a new forum post."""
    try:
        # Verify user exists
        user = await User.get(ObjectId(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        post_data = {
            "title": payload.title,
            "content": payload.content,
            "author": ObjectId(user_id),
            "type": payload.type,
        }
        
        if payload.messId:
            post_data["messId"] = ObjectId(payload.messId)
        
        if payload.type == 'poll' and payload.pollOptions:
            post_data["pollOptions"] = [
                {"text": option, "votes": []} 
                for option in payload.pollOptions
            ]
        
        post = ForumPost(**post_data)
        await post.insert()
        
        return post.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get all posts with filters and pagination
@router.get("/posts")
async def get_posts(
    messId: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """Get forum posts with filters and pagination."""
    try:
        query = {}
        
        if messId:
            query["messId"] = ObjectId(messId)
        if type:
            query["type"] = type
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"content": {"$regex": search, "$options": "i"}}
            ]
        
        # Get total count
        total_posts = await ForumPost.find(query).count()
        total_pages = math.ceil(total_posts / limit)
        skip = (page - 1) * limit
        
        # Get posts
        posts = await ForumPost.find(query).sort("-createdAt").skip(skip).limit(limit).to_list()
        
        # Populate author and messId
        result_posts = []
        for post in posts:
            post_dict = post.to_dict()
            
            # Populate author
            author = await User.get(post.author)
            if author:
                post_dict["author"] = {"_id": str(author.id), "username": author.username}
            
            # Populate messId
            if post.messId:
                mess = await Mess.get(post.messId)
                if mess:
                    post_dict["messId"] = {"_id": str(mess.id), "Mess_Name": mess.Mess_Name}
                else:
                    post_dict["messId"] = None
            else:
                post_dict["messId"] = None
            
            # Populate comment user info
            for comment in post_dict.get("comments", []):
                if "userId" in comment:
                    try:
                        comment_user = await User.get(ObjectId(comment["userId"]))
                        if comment_user:
                            comment["userId"] = {"_id": str(comment_user.id), "username": comment_user.username}
                    except:
                        pass
            
            result_posts.append(post_dict)
        
        return {
            "posts": result_posts,
            "pagination": {
                "currentPage": page,
                "totalPages": total_pages,
                "totalPosts": total_posts,
                "hasNextPage": page < total_pages,
                "hasPrevPage": page > 1
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Add comment
@router.post("/posts/{post_id}/comment/{user_id}")
async def add_comment(post_id: str, user_id: str, payload: AddCommentRequest):
    """Add a comment to a post."""
    try:
        post = await ForumPost.get(ObjectId(post_id))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        user = await User.get(ObjectId(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        comment = {
            "_id": str(ObjectId()),
            "userId": user_id,
            "content": payload.content,
            "likes": [],
            "createdAt": datetime.utcnow().isoformat()
        }
        
        if not post.comments:
            post.comments = []
        post.comments.append(comment)
        post.updatedAt = datetime.utcnow()
        await post.save()
        
        # Return populated post
        post_dict = post.to_dict()
        author = await User.get(post.author)
        if author:
            post_dict["author"] = {"_id": str(author.id), "username": author.username}
        
        # Populate messId
        if post.messId:
            mess = await Mess.get(post.messId)
            if mess:
                post_dict["messId"] = {"_id": str(mess.id), "Mess_Name": mess.Mess_Name}
        
        # Populate comment users
        for c in post_dict.get("comments", []):
            if "userId" in c:
                try:
                    comment_user = await User.get(ObjectId(c["userId"]))
                    if comment_user:
                        c["userId"] = {"_id": str(comment_user.id), "username": comment_user.username}
                except:
                    pass
        
        return post_dict
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Vote on poll
@router.post("/posts/{post_id}/vote/{user_id}")
async def vote_poll(post_id: str, user_id: str, payload: VotePollRequest):
    """Vote on a poll option."""
    try:
        post = await ForumPost.get(ObjectId(post_id))
        if not post or not post.isPollActive or not post.pollOptions:
            raise HTTPException(status_code=404, detail="Poll not found or inactive")
        
        user = await User.get(ObjectId(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Remove previous vote
        for option in post.pollOptions:
            option["votes"] = [v for v in option.get("votes", []) if v != user_id]
        
        # Add new vote
        if 0 <= payload.optionIndex < len(post.pollOptions):
            if "votes" not in post.pollOptions[payload.optionIndex]:
                post.pollOptions[payload.optionIndex]["votes"] = []
            post.pollOptions[payload.optionIndex]["votes"].append(user_id)
        
        post.updatedAt = datetime.utcnow()
        await post.save()
        
        return post.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Like/Unlike post
@router.post("/posts/{post_id}/like/{user_id}")
async def like_post(post_id: str, user_id: str):
    """Toggle like on a post."""
    try:
        post = await ForumPost.get(ObjectId(post_id))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        user_oid = ObjectId(user_id)
        
        if user_oid in post.likes:
            post.likes.remove(user_oid)
        else:
            post.likes.append(user_oid)
        
        post.updatedAt = datetime.utcnow()
        await post.save()
        
        return post.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Like/Unlike comment
@router.post("/posts/{post_id}/comments/{comment_id}/like/{user_id}")
async def like_comment(post_id: str, comment_id: str, user_id: str):
    """Toggle like on a comment."""
    try:
        post = await ForumPost.get(ObjectId(post_id))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        comment = None
        for c in post.comments:
            if c.get("_id") == comment_id:
                comment = c
                break
        
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        if "likes" not in comment:
            comment["likes"] = []
        
        if user_id in comment["likes"]:
            comment["likes"].remove(user_id)
        else:
            comment["likes"].append(user_id)
        
        post.updatedAt = datetime.utcnow()
        await post.save()
        
        return post.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Delete comment
@router.delete("/posts/{post_id}/comments/{comment_id}/{user_id}")
async def delete_comment(post_id: str, comment_id: str, user_id: str):
    """Delete a comment from a post."""
    try:
        post = await ForumPost.get(ObjectId(post_id))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        comment = None
        comment_index = None
        for i, c in enumerate(post.comments):
            if c.get("_id") == comment_id:
                comment = c
                comment_index = i
                break
        
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        if comment.get("userId") != user_id:
            raise HTTPException(status_code=403, detail="You can only delete your own comments")
        
        post.comments.pop(comment_index)
        post.updatedAt = datetime.utcnow()
        await post.save()
        
        return post.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Update post
@router.put("/posts/{post_id}/{user_id}")
async def update_post(post_id: str, user_id: str, payload: UpdatePostRequest):
    """Update a forum post."""
    try:
        post = await ForumPost.get(ObjectId(post_id))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        if str(post.author) != user_id:
            raise HTTPException(status_code=403, detail="You can only edit your own posts")
        
        post.title = payload.title
        post.content = payload.content
        post.type = payload.type
        
        if payload.type == 'poll' and payload.pollOptions:
            # Keep existing votes for unchanged options
            new_poll_options = []
            for option_text in payload.pollOptions:
                existing = None
                if post.pollOptions:
                    for opt in post.pollOptions:
                        if opt.get("text") == option_text:
                            existing = opt
                            break
                
                if existing:
                    new_poll_options.append(existing)
                else:
                    new_poll_options.append({"text": option_text, "votes": []})
            
            post.pollOptions = new_poll_options
        
        post.updatedAt = datetime.utcnow()
        await post.save()
        
        return post.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Delete post
@router.delete("/posts/{post_id}/{user_id}")
async def delete_post(post_id: str, user_id: str):
    """Delete a forum post."""
    try:
        post = await ForumPost.get(ObjectId(post_id))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        if str(post.author) != user_id:
            raise HTTPException(status_code=403, detail="You can only delete your own posts")
        
        await post.delete()
        
        return {"message": "Post deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
