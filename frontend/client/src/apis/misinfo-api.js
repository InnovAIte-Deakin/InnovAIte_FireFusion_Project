import axiosClient from "../apis/axios-client"
const baseUrlNarratives = 'misinformation/narratives';
const baseUrlPosts = 'misinformation/posts';

const narrativesApi = {
  getAll: () => axiosClient.get(baseUrlNarratives),
  getOne: (narrative_id) => axiosClient.get(`${baseUrlNarratives}/${narrative_id}`)
};

const postsApi = {
  getAll: () => axiosClient.get(baseUrlPosts),
  getOne: (post_id) => axiosClient.get(`${baseUrlPosts}/${post_id}`)
};

export {postsApi};
export default narrativesApi;