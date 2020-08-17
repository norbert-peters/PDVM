import React, { useState } from "react"

import { GetPost } from '../dataapi/Post'

import {PostEditForm}  from '../components/PostEditForm'


function checkCreate(pdvm, isCreate, setIsCreate) {
  if (pdvm==='new' && !isCreate) {
    console.log('check angekommen')
    setIsCreate(true) 
  }
  return
}


export default function PostEdit(props) {
  const [isCreate, setIsCreate] = useState(false)

  var post = {}

  checkCreate(props.pdvm, isCreate, setIsCreate)

  if (!isCreate) {
    const { query, status, isLoading, data, isError, error } = GetPost(props.id)
    console.log('Bestand GetPost',
      query, '||',
      status, '||',
      isLoading, '||',
      data, '||',
      isError, '||',
      error, '||'
    )

    if (isError) {
      return <div>{error.message}</div> // error state
    }

    if (isLoading) {
      return <div>Daten werden geladen...</div> // loading state
    }

    post = data

  } else {
    post = props
  }

  console.log('Mitte', post)

  //initialFormFields(formFields, post, props)

  return (
    <PostEditForm 
      post={post} 
      isCreate={isCreate}
    />
  )

}
