import React, { useState } from 'react'

import { GetPost } from '../dataapi/Post'
import { GetComment } from '../dataapi/Comment'
import  CommentEdit  from '../components/CommentEdit'
import  { Post }  from '../components/Post'
import { PdvmSection } from '../pdvmComponents/PdvmSection'
import { PdvmFlexBox } from '../pdvmComponents/PdvmFlexBox'

function checkCreate(pdvm, isCreate, setIsCreate) {
  if (pdvm==='new' && !isCreate) {
    setIsCreate(true) 
  }
  return
}


function pdvmGetPost(id) {
  const { isLoading, data, isError, error } = GetPost(id)
  if (isError) {
    return <div>{error.message}</div> // error state
  }

  if (isLoading) {
    return <div>Daten werden geladen...</div> // loading state
  }
  
  return data
}

/*
Hier beginnt der eigentliche Edit Dialog
*/
const EditCommentPage = ({ match }) => {
  let comment = {
    id: match.params.id,
    postId: match.params.postId,
    name: "",
    email: "",
    body: "",
    pdvm: match.params.pdvm,
    ret: "-1"
  }

  const [isCreate, setIsCreate] = useState(false)
  var post = ""

  checkCreate(comment.pdvm, isCreate, setIsCreate)
  if (match.params.pdvm === 'mod') {
    post = pdvmGetPost(match.params.postId)
  }
  const renderPost = () => {
    if (match.params.pdvm === 'new') {
      post = pdvmGetPost(match.params.postId)
    }
    return <Post post={post} />
  }

  if (!isCreate) {
    const { isLoading, data, isError, error } = GetComment(comment.id)

    if (isError) {
      return <div>{error.message}</div> // error state
    }

    if (isLoading) {
      return <div>Daten werden geladen...</div> // loading state
    }

    comment.id = data.id
    comment.postId = data.postId
    comment.name = data.name
    comment.email = data.email
    comment.body = data.body
  }


  const renderComment = () => {
    return <CommentEdit 
      comment={comment}
      isCreate={isCreate}
    />
  }

  const renderTitel = () => {
    if (comment.pdvm === 'mod') {
      return <PdvmFlexBox>Kommentar modifizieren</PdvmFlexBox>
    } else if (comment.pdvm === 'new') {
      return <PdvmFlexBox>Kommentar anlegen</PdvmFlexBox>
    } else {
      return <PdvmFlexBox>Die Art des Kommentares konnte nicht ermittelt werden</PdvmFlexBox>
    }
  }

  return (
    <PdvmSection>
      {renderPost()}
      {renderTitel()}
      {renderComment()}
    </PdvmSection>
  )
}

export default EditCommentPage

