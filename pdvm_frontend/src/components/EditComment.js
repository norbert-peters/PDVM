import React from 'react'

export const EditComment = ({ comment }) => (
    <aside className="comment">
        <h2>{comment.title}</h2>
        <h3>{comment.email}</h3>
        <p>{comment.body}</p>
    </aside>
)
