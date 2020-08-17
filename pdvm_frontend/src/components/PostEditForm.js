import React, { useState } from "react"

import { PostPost, PutPost } from '../dataapi/Post'
import { PdvmButton } from '../pdvmComponents/PdvmButton'
import PdvmInputControl  from '../pdvmComponents/PdvmInputControl'

function useFormFields(initialValues) {
    const [formFields, setFormFields] = useState(initialValues);
    
    const createChangeHandler = (key) => (
      val: React.ChangeEvent<HTMLInputElement>,
    ) => {
      const value = val;
      setFormFields((prev) => ({ ...prev, [key]: value }));
    };
  
    return { formFields, createChangeHandler };
  }

  const initialFormFields = (formFields, post) =>{
    if (formFields.id ==="") {
      formFields.id = post.id === undefined ? "" : post.id
      formFields.userId = post.userId=== undefined ? "88" : post.userId
      formFields.title = post.title=== undefined ? "" : post.title
      formFields.body = post.body=== undefined ? "" : post.body
      console.log('xxff2', post, formFields)
    } else {
      formFields.id = post.id
      formFields.userId = post.userId
      formFields.title = post.title
      formFields.body = post.body
    }
    console.log('xxff2', post, formFields)
  }


export function PostEditForm(props) {
    const { formFields, createChangeHandler } = useFormFields({
        id: "",
        userId: "",
        title: "",
        body: "",
        })
    
  const [mutate_post] = PostPost(formFields)
  const [mutate_put] = PutPost(formFields)
  
  const [isFirst, setIsFirst] = useState(true)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('FormFields', formFields)
    if (props.isCreate) {
      console.log('mutate_post', formFields)
      mutate_post(formFields)
    } else {
      console.log('mutate_put', formFields)
      mutate_put(formFields)
    }
  }

  if (isFirst) {
    initialFormFields(formFields, props.post)
    setIsFirst(false) 
  }

  return (
    <form onSubmit={handleSubmit}>
        <PdvmInputControl
          pdvmType='text'
          maxLength="50"
          type="text"
          label="Titel"
          value={formFields.title}
          onChange={createChangeHandler("title")}
        />
        <PdvmInputControl
          pdvmType="textaria"
          type="text"
          label="Artikel"
          value={formFields.body}
          onChange={createChangeHandler("body")}
        />
      <PdvmButton>Speichern</PdvmButton>
    </form>
  )
}