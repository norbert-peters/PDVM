import React from "react";
import { useForm } from "react-hook-form";

import { putComment } from '../slices/comment'


export default function CommentEdit(props) {
  const { register, handleSubmit, errors } = useForm({
      defaultValues: {
        id: props.comment.id,
        postId: props.comment.postId,
        name: props.comment.name,
        email: props.comment.email,
        body: props.comment.body,
      }  
  })
  const onSubmit = (data) => {
    const npres = {
      id: props.comment.id,
      postId: props.comment.postId,
      name: data.name,
      email: data.email,
      body: data.body,    
    }
    
    const xyz = putComment(npres, npres["id"]);
    console.log(xyz)
    alert(JSON.stringify("Die Änderung wurde gespeichert"));
  }

  
  /*const onSubmit = data => ({
    comment: {
      "name": data.name,
      "email": data.email,
      "body": data.body,
    }
  }

  )*/
//  const onSubmit = data => (
//    console.log(data)
//  )  
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <label>Name</label>
      <input
        type="text"
        aria-invalid={errors.name ? "true" : "false"}
        aria-describedby="nameError"
        name="name"
        
//        defaultValue={props.comment.name}
        ref={register({ required: true })}
      />
      <span id="NameError" style={{ display: errors.name ? "block" : "none" }}>
        Das Feld Name ist erforderlich
      </span>
      <label>Email-Adresse</label>
      <input
        type="email"
        aria-invalid={errors.email ? "true" : "false"}
        aria-describedby="mailError"
        name="email"
//        defaultValue={props.comment.email}
        ref={register({ required: true })}
      />
      <span id="mailError" style={{ display: errors.email ? "block" : "none" }}>
        Das Feld Mail ist erforderlich
      </span>
      <label>Kommentar</label>
      <textarea
        type="textarea"
        aria-invalid={errors.body ? "true" : "false"}
        aria-describedby="bodyError"
        name="body"
//        defaultValue={props.comment.body}
//        multiLine="true"
        ref={register({ required: true })}
      />
      <span id="bodyError" style={{ display: errors.body ? "block" : "none" }}>
        Das Feld Kommentar ist erforderlich
      </span>
      <br />


      <input type="submit" />
    </form>
  );
} 

/*
import React from 'react'
import { Field, reduxForm } from "redux-form";

const validate = values => {
  const errors = {};
*/
/*  if (!values.username) {
    errors.username = "Required";
  } else if (values.username === "admin") {
    errors.username = "Nice try!";
  }
*/
/*  if (!/^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i.test(values.email)) {
    errors.email = "Keine gültige Email-Adresse";
  }

  return errors;
};

const renderField = ({ input, label, type, value, name, meta: { touched, error } }) => (
  <>
    <input {...input} placeholder={label} type={type} value={value} />
    {touched && error && <span>{error}</span>}
  </>
);

const Form = props => {
  const { handleSubmit } = props;
  const onSubmit = values => console.log(values);
  console.log(props)
  console.log(props.comment.name)
  console.log(props.comment.email)
  console.log(props.comment.body)

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Field name={props.comment.name} value={props.comment.name} type="text" component={renderField} label="Name" /> <br />
      <Field name="comment.email" value="props.comment.email" type="email" component={renderField} label="Email" /> <br />
      <Field name="comment.body" value="props.comment.body" component={renderField} label="Kommentar" /> <br />
    
      <button type="submit">Submit</button>
    </form>
  );
};

export const CommentEdit = reduxForm({ form: "syncValidation", validate })(Form);
*/

/*export const CommentEdit = ({ comment }) => (
  <aside className="comment">
    <h2>{comment.name}</h2>
    <h3>{comment.email}</h3>
    <p>{comment.body}</p>
  </aside>
)
*/