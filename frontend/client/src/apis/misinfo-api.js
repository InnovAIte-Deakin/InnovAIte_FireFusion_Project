import axiosClient from "../apis/axios-client"

const baseUrlNarratives = '/misinformation/narratives';
const baseUrlPosts = '/misinformation/posts';
const baseUrlIncidents = '/misinformation/incidents';

const narrativesApi = {
  getAll: () => axiosClient.get(baseUrlNarratives),
  getOne: (narrative_id) => axiosClient.get(`${baseUrlNarratives}/${narrative_id}`)
};

export const postsApi = {
  getAll: () => axiosClient.get(baseUrlPosts),
  getOne: (post_id) => axiosClient.get(`${baseUrlPosts}/${post_id}`)
};

export const incidentsApi = {
  getAll: () => axiosClient.get(baseUrlIncidents),
  getOne: (incident_id) => axiosClient.get(`${baseUrlIncidents}/${incident_id}`)
};

export default narrativesApi;