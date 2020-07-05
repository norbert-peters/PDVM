// angepasst auf fetch(get bereits verwendet), byURL ergänzt
// ----------------------------------------------------------------------------
import { createSlice } from '@reduxjs/toolkit'
import axios from 'axios'

const API_URL = 'http://localhost:8000'

export const initialState = {
  nextPageURL: '',
  prevPageURL: '',
  numPages: 0,
  count: 0,
  loading: false,
  hasErrors: false,
  posts: [],
}

const postsSlice = createSlice({
  name: 'posts',
  initialState,
  reducers: {
    getPosts: state => {
      state.loading = true
    },
    getPostsSuccess: (state, { payload }) => {
      console.log('getSuccess ', payload)
      state.posts = payload.data
      state.nextPageURL = payload.nextlink
      state.prevPageURL = payload.prevlink
      state.numPages = payload.numpages
      state.count = payload.count
      state.pageNumber = payload.pagenumber
      state.loading = false
      state.hasErrors = false
    },
    getPostsFailure: state => {
      state.loading = false
      state.hasErrors = true
    },
  },
})

export const { getPosts, getPostsSuccess, getPostsFailure } = postsSlice.actions
export const postsSelector = state => state.posts
export default postsSlice.reducer


export function fetchPosts() {
  return async dispatch => {
    dispatch(getPosts())

    try {
      const response = await axios.get(`${API_URL}/api/posts/`)
      const data = await response.data
      dispatch(getPostsSuccess(data))
    } catch (error) {
      dispatch(getPostsFailure())
    }
  }
}

export function getPostsByURL(link) {
  return async dispatch => {
    dispatch(getPosts())
    try {
      const response = await axios.get(`${API_URL}${link}`)
      const data = await response.data
      dispatch(getPostsSuccess(data))
    } catch (error) {
      dispatch(getPostsFailure())
    }
  }
}
