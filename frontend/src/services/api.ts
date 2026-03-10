import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type {
  NewsTask,
  NewsTaskCreate,
  NewsTaskUpdate,
  Source,
  SourceCreate,
  SourceUpdate,
  SourceNewsTaskAssociation,
  NewsItem,
  NewsItemNewsTask,
  Newspaper,
} from '../types';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface User {
  id: number;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: import.meta.env.VITE_API_URL || '/api',
    prepareHeaders: (headers) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['User', 'NewsTasks', 'Sources', 'Associations', 'NewsItems', 'Newspaper'],
  endpoints: (builder) => ({
    register: builder.mutation<User, RegisterRequest>({
      query: (credentials) => ({
        url: '/auth/register',
        method: 'POST',
        body: credentials,
      }),
    }),
    login: builder.mutation<LoginResponse, LoginRequest>({
      query: (credentials) => {
        const formData = new FormData();
        formData.append('username', credentials.username);
        formData.append('password', credentials.password);
        return {
          url: '/auth/jwt/login',
          method: 'POST',
          body: formData,
        };
      },
      invalidatesTags: ['User'],
    }),
    logout: builder.mutation<void, void>({
      query: () => ({
        url: '/auth/jwt/logout',
        method: 'POST',
      }),
    }),
    getCurrentUser: builder.query<User, void>({
      query: () => '/users/me',
      providesTags: ['User'],
    }),

    // News Tasks
    getNewsTasks: builder.query<NewsTask[], void>({
      query: () => '/news-tasks',
      providesTags: ['NewsTasks'],
    }),
    getNewsTask: builder.query<NewsTask, string>({
      query: (id) => `/news-tasks/${id}`,
      providesTags: (_result, _error, id) => [
        { type: 'NewsTasks', id }
      ],
    }),
    createNewsTask: builder.mutation<NewsTask, NewsTaskCreate>({
      query: (body) => ({
        url: '/news-tasks',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['NewsTasks'],
    }),
    updateNewsTask: builder.mutation<
      NewsTask,
      { id: string; data: NewsTaskUpdate }
    >({
      query: ({ id, data }) => ({
        url: `/news-tasks/${id}`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: 'NewsTasks', id },
        'NewsTasks',
      ],
    }),
    deleteNewsTask: builder.mutation<void, string>({
      query: (id) => ({
        url: `/news-tasks/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['NewsTasks'],
    }),

    // Sources
    getSources: builder.query<Source[], void>({
      query: () => '/sources',
      providesTags: ['Sources'],
    }),
    searchSources: builder.query<Source[], string>({
      query: (q) => `/sources/search?q=${encodeURIComponent(q)}`,
      providesTags: ['Sources'],
    }),
    getSource: builder.query<Source, string>({
      query: (id) => `/sources/${id}`,
      providesTags: (_result, _error, id) => [{ type: 'Sources', id }],
    }),
    createSource: builder.mutation<Source, SourceCreate>({
      query: (body) => ({
        url: '/sources',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Sources'],
    }),
    updateSource: builder.mutation<
      Source,
      { id: string; data: SourceUpdate }
    >({
      query: ({ id, data }) => ({
        url: `/sources/${id}`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: ['Sources'],
    }),
    deleteSource: builder.mutation<void, string>({
      query: (id) => ({
        url: `/sources/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Sources'],
    }),

    // Associations
    getTaskSources: builder.query<
      SourceNewsTaskAssociation[],
      string
    >({
      query: (taskId) => `/associations/task/${taskId}`,
      providesTags: ['Associations'],
    }),
    associateSourceWithTask: builder.mutation<
      SourceNewsTaskAssociation,
      SourceNewsTaskAssociation
    >({
      query: (body) => ({
        url: '/associations',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Associations'],
    }),
    disassociateSourceFromTask: builder.mutation<
      void,
      { sourceId: string; taskId: string }
    >({
      query: ({ sourceId, taskId }) => ({
        url: `/associations/${sourceId}/${taskId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Associations'],
    }),

    // News Items
    getNewsItems: builder.query<
      NewsItem[],
      {
        skip?: number;
        limit?: number;
        source_id?: number;
      }
    >({
      query: (params) => ({
        url: '/news-items',
        params,
      }),
      providesTags: ['NewsItems'],
    }),
    getNewsItem: builder.query<NewsItem, string>({
      query: (id) => `/news-items/${id}`,
      providesTags: (_result, _error, id) => [{ type: 'NewsItems', id }],
    }),

    // News Item News Task (processing results)
    getNewsItemResults: builder.query<NewsItemNewsTask[], number>({
      query: (newsItemId) => `/news-items/${newsItemId}/results`,
      providesTags: (_result, _error, newsItemId) => [
        { type: 'NewsItems', id: newsItemId },
      ],
    }),

    // Newspaper
    getPublicFrontpageNewspaper: builder.query<Newspaper, void>({
      query: () => '/newspapers/frontpage',
      providesTags: ['Newspaper'],
    }),

    getNewspaper: builder.query<Newspaper, number>({
      query: (taskId) => `/newspapers/${taskId}`,
      providesTags: (_result, _error, taskId) => [
        { type: 'Newspaper', id: taskId },
      ],
    }),

    regenerateNewspaper: builder.mutation<Newspaper, number>({
      query: (taskId) => ({
        url: `/newspapers/${taskId}/regenerate`,
        method: 'POST',
      }),
      invalidatesTags: (_result, _error, taskId) => [
        { type: 'Newspaper', id: taskId },
      ],
    }),
  }),
});

export const {
  useRegisterMutation,
  useLoginMutation,
  useLogoutMutation,
  useGetCurrentUserQuery,
  useGetNewsTasksQuery,
  useGetNewsTaskQuery,
  useCreateNewsTaskMutation,
  useUpdateNewsTaskMutation,
  useDeleteNewsTaskMutation,
  useGetSourcesQuery,
  useSearchSourcesQuery,
  useLazySearchSourcesQuery,
  useGetSourceQuery,
  useCreateSourceMutation,
  useUpdateSourceMutation,
  useDeleteSourceMutation,
  useGetTaskSourcesQuery,
  useAssociateSourceWithTaskMutation,
  useDisassociateSourceFromTaskMutation,
  useGetNewsItemsQuery,
  useGetNewsItemQuery,
  useGetNewsItemResultsQuery,
  useGetPublicFrontpageNewspaperQuery,
  useGetNewspaperQuery,
  useRegenerateNewspaperMutation,
} = api;
