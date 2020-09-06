import React, { useState } from "react"

import { PostComment, PutComment } from '../dataapi/Comment'
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

  const initialFormFields = (formFields, comment) =>{
    formFields.id = comment.id === undefined ? "" : comment.id
    formFields.postId = comment.postId=== undefined ? "88" : comment.postId
    formFields.name = comment.name=== undefined ? "" : comment.name
    formFields.email = comment.email===undefined ? "" : comment.email
    formFields.body = comment.body=== undefined ? "" : comment.body
    formFields.pdvm = comment.pdvm
    formFields.ret = comment.ret
  }

/*
Hier beginnt die default Funktion
*/

export default function CommentEdit(props) {
  const { formFields, createChangeHandler } = useFormFields({
      id: "",
      postId: "",
      name: "",
      email: "",
      body: "",
      pdvm: "",
      ret: "-1",
      })
    
  const [mutate_post] = PostComment(formFields)
  const [mutate_put] = PutComment(formFields)

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
    initialFormFields(formFields, props.comment)
    setIsFirst(false) 
  }

  return (
    <form onSubmit={handleSubmit}>
      <PdvmInputControl
        autoFocus={true}
        pdvmType='textonly'
        maxLength="50"
        type="text"
        label="Name"
        value={formFields.name}
        onChange={createChangeHandler("name")}
        num="0"
        id="1"
      />
      <PdvmInputControl
        autoFocus={false}
        pdvmType='textonly'
        maxLength="50"
        type="email"
        label="Email"
        value={formFields.email}
        onChange={createChangeHandler("email")}
        num="1"
        id="2"
      />
      <PdvmInputControl
        autoFocus={false}
        pdvmType="textarea"
        type="text"
        label="Kommentar"
        value={formFields.body}
        onChange={createChangeHandler("body")}
        num="2"
        id="3"
      />
      <PdvmButton >
        Speichern
      </PdvmButton>
    </form>
  );
}