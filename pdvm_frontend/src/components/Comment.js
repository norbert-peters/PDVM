import React from 'react'
import { Link } from 'react-router-dom'

export const Comment = ({ comment }) => (
  <aside className="comment">
    <h2>{comment.name}</h2>
    <h3>{comment.email}</h3>
    <p>{comment.body}</p>
    <Link to={`/postsedit/${comment.id}/${comment.postId}`} className="button">
          ändern
    </Link>
  </aside>
)

