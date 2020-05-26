// src/actions/postsActions.js
// ----------------------------------------------------------------------------

// statt fetch wird axios verwendet
import axios from 'axios'

// Redux Aktionstypen werden erstellt
export const GET_POSTS = 'GET POSTS'
export const GET_POSTS_SUCCESS = 'GET_POSTS_SUCCESS'
export const GET_POSTS_FAILURE = 'GET_POSTS_FAILURE'

// Redux Aktionen werden erstellt und dann zurück gegeben
export const getPosts = () => ({
    type: GET_POSTS,
  })
  
export const getPostsSuccess = posts => ({
    type: GET_POSTS_SUCCESS,
    payload: posts,
  })
  
export const getPostsFailure = () => ({
    type: GET_POSTS_FAILURE,
  })


// Kombination und asynchrone Rückgabe
export function fetchPosts() {
    return async dispatch => {
      dispatch(getPosts())
  
      try {
        const response = await axios.get('https://jsonplaceholder.typicode.com/posts');
        console.log(response);     // zur Kontrolle der API
        const data = await response.data
  
        dispatch(getPostsSuccess(data))
      } catch (error) {
        dispatch(getPostsFailure())
      }
    }
  }  