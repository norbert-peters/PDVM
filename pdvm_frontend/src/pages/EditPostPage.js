import React, { useState } from 'react'

import PostEdit from '../components/PostEdit'
import { GetPost } from '../dataapi/Post'
import { PdvmSection } from '../pdvmComponents/PdvmSection'

function checkCreate(pdvm, isCreate, setIsCreate) {
  if (pdvm==='new' && !isCreate) {
    setIsCreate(true) 
  }
  return
}

/*
Hier beginnt die Seite. Der Bereich zum eigentlichen Editieren befindet sich in PostEditForm.

*/
const EditPostPage = ({ match }) => {
console.log('Match: ',match)
  let post = {
      id: match.params.id,
      userId: "-1",
      title: "",
      body: "",
      pdvm: match.params.pdvm,
      ret: "-1"
    }

  const [isCreate, setIsCreate] = useState(false)
  
  checkCreate(post.pdvm, isCreate, setIsCreate)
  
  if (!isCreate) {
    const { isLoading, data, isError, error } = GetPost(post.id)

    if (isError) {
      return <div>{error.message}</div> // error state
    }

    if (isLoading) {
      return <div>Daten werden geladen...</div> // loading state
    }

    post.id = data.id
    post.userId = data.userId
    post.title = data.title
    post.body = data.body
  }

  const renderPost = (
    <PostEdit 
      post={post} 
      isCreate={isCreate}
    />
  )

  const renderTitel = () => {
    if (post.pdvm === 'mod') {
      return <h1>Artikel modifizieren</h1>
    } else if (post.pdvm === 'new') {
      return <h1>Artikel anlegen</h1>
    } else {
      return <h1>Die Art des Artikels konnte nicht ermittelt werden</h1>
    }
  }

  return (
    <PdvmSection>
      {renderTitel()}
      {renderPost}
    </PdvmSection>
  )
}

export default EditPostPage
