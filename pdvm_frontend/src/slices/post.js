import { createSlice } from '@reduxjs/toolkit'
import axios from 'axios'

export const initialState = {
  loading: false,
  hasErrors: false,
  post: {},
}

const postSlice = createSlice({
  name: 'post',
  initialState,
  reducers: {
    getPost: state => {
      state.loading = true
      state.creating = false
    },
    getPostSuccess: (state, { payload }) => {
      state.post = payload
      state.creating = false
      state.loading = false
      state.hasErrors = false
    },
    getPostFailure: state => {
      state.loading = false
      state.creating = false
      state.hasErrors = true
    },
    getPostCreate: state => {
      state.loading = false
      state.creating = true
      state.hasErrors = false
    },
  },
})

export const { 
  getPost, 
  getPostSuccess, 
  getPostFailure,
  getPostCreate,
} = postSlice.actions
export const postSelector = state => state.post
export default postSlice.reducer

export function fetchPost(id) {
  return async dispatch => {
    dispatch(getPost())

    try {
      const response = await axios.get(
        `http://localhost:8000/api/posts/${id}`
      )
      console.log(response)
      const data = await response.data

      dispatch(getPostSuccess(data))
    } catch (error) {
      dispatch(getPostCreate())
    }
  }
}

export function putPost(id, post) {
  return async dispatch => {
    dispatch(getPost())

    try {
      const response = await axios.put(
        `http://localhost:8000/api/posts/${id}`, post
      )
      const data = await response.data
      console.log('nach Aufruf PUT')
      console.log(data)
      dispatch(getPostSuccess(data))
    } catch (error) {
      dispatch(getPostFailure())
    }
  }
}

export function postPost(post) {
  return async dispatch => {
    dispatch(getPost())

    try {
      const response = await axios.post(
        `http://localhost:8000/api/posts/`, post
      )
      const data = await response.data
      console.log('nach Aufruf POST')
      console.log(data)
      dispatch(getPostSuccess(data))
    } catch (error) {
      dispatch(getPostFailure())
    }
  }
}
