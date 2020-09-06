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
    formFields.id = post.id === undefined ? "" : post.id
    formFields.userId = post.userId=== undefined ? "88" : post.userId
    formFields.title = post.title=== undefined ? "" : post.title
    formFields.body = post.body=== undefined ? "" : post.body
    formFields.pdvm = post.pdvm
    formFields.ret = post.ret
  }

/*
Hier beginnt die default Funktion
*/

export default function PostEdit(props) {
  const { formFields, createChangeHandler } = useFormFields({
      id: "",
      userId: "",
      title: "",
      body: "",
      pdvm: "",
      ret: "-1",
      })
    
  const [mutate_post] = PostPost(formFields)
  const [mutate_put] = PutPost(formFields)

  const [firstPdvm, setFirstPdvm] = useState(true)
  const [isFirst, setIsFirst] = useState(true)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (props.isCreate) {
      if (formFields.ret === "0" && firstPdvm) {
        setFirstPdvm(false)
        mutate_put(formFields)
      } else {
      if (firstPdvm) {
        mutate_post(formFields)
      } else {
        mutate_put(formFields)
      }}
    } else {
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
          pdvmType='textonly'
          maxLength="50"
          type="text"
          label="Titel"
          value={formFields.title}
          onChange={createChangeHandler("title")}
        />
        <PdvmInputControl
          pdvmType="textarea"
          type="text"
          label="Artikel"
          value={formFields.body}
          onChange={createChangeHandler("body")}
        />
      <PdvmButton >
        Speichern
      </PdvmButton>
    </form>
  )
}