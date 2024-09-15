import { useQuery } from "react-query";
import axios from 'axios'

const API_URL = 'http://localhost:8000'

const getPosts = async (key, nlink) => {
  const link = nlink ? nlink : '/api/posts/'
  const { data } = await axios.get(
    `${API_URL}${link}`
  )
  return data
}

export default function usePosts(nlink) {
  return useQuery(['posts', nlink ], getPosts)
}
