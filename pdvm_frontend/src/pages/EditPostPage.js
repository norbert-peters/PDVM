import React from 'react'

import PostEdit from '../components/PostEdit'
import { PdvmSection } from '../pdvmComponents/PdvmSection'


const EditPostPage = ({ match }) => {
console.log('Match: ',match)
  const post = {
      id: match.params.id,
      userId: match.params.userId,
      title: match.params.title,
      body: match.params.body,
      pdvm: match.params.pdvm,
    }


  const renderPost = (
    <PostEdit 
      id={post.id} 
      userId={post.userId} 
      title={post.title} 
      body={post.body} 
      pdvm={post.pdvm}
    />
  )

  function renderTitel(pdvm) {
    if (pdvm === 'mod') {
      return <h1>Artikel modifizieren</h1>
    } else if (pdvm === 'new') {
      return <h1>Artikel anlegen</h1>
    } else {
      return <h1>Die Art des Artikels konnte nicht ermittelt werden</h1>
    }
  }

  return (
    <PdvmSection>
        {renderTitel(post.pdvm)}
        {renderPost}
    </PdvmSection>
  )
}

export default EditPostPage
