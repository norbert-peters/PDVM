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
    },
    getPostSuccess: (state, { payload }) => {
      state.post = payload
      state.loading = false
      state.hasErrors = false
    },
    getPostFailure: state => {
      state.loading = false
      state.hasErrors = true
    },
  },
})

export const { getPost, getPostSuccess, getPostFailure } = postSlice.actions
export const postSelector = state => state.post
export default postSlice.reducer

export function fetchPost(id) {
  return async dispatch => {
    dispatch(getPost())

    try {
      const response = await axios.get(
        `http://localhost:8000/api/posts/${id}`
      )
      //console.log(response)
      const data = await response.data

      dispatch(getPostSuccess(data))
    } catch (error) {
      dispatch(getPostFailure())
    }
  }
}
