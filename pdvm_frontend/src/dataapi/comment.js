import React from "react";
//import { useQuery } from "react-query";
import axios from "axios";

export const fetchNComments = (id) => {
    const { data } = axios.get(
        `http://localhost:8000/api/comments/${id}`
      )
return data;
};


/*
export function fetchComment(id) {
    return async dispatch => {
      dispatch(getComment())
  
      try {
        const response = await axios.get(
          `http://localhost:8000/api/comments/${id}`
        )
        const data = await response.data
        dispatch(getCommentSuccess(data))
      } catch (error) {
        dispatch(getCommentCreate())
      }
    }
  }
  
  export function putComment(id, comment) {
    return async dispatch => {
      dispatch(getComment())
  
      try {
        const response = await axios.put(
          `http://localhost:8000/api/comments/${id}`, comment
        )
        const data = await response.data
        dispatch(getCommentSuccess(data))
      } catch (error) {
        dispatch(getCommentFailure())
      }
    }
  }
  
  export function postComment(comment) {
    return async dispatch => {
      dispatch(getComment())
  
      try {
        const response = await axios.post(
          `http://localhost:8000/api/comments/`, comment
        )
        const data = await response.data
        console.log('nach Aufruf POST')
        console.log(data)
        dispatch(getCommentSuccess(data))
      } catch (error) {
        dispatch(getCommentFailure())
      }
    }
  }

*/
/*const App = () => {
  const { data } = useQuery("todos", fetchTodos);

  return data ? (
    <ul>{data.length > 0 && data.map((todo) => <li>{todo.text}</li>)}</ul>
  ) : null;
};*/