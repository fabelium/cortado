import type { ChatResponse } from '~~/shared/types/outputs'
import { expectOk } from '~/utils/expectOk'

export function useChatClient() {
  const { $api } = useNuxtApp()

  // Contract body is {query, selection} (contract/schema/request.schema.json):
  // the chat is stateless server-side, so no history is sent.
  async function sendMessage(selection: string[], query: string): Promise<ChatResponse> {
    return expectOk(await $api<ChatResponse>('/chat', {
      method: 'POST',
      body: { query, selection },
    }))
  }

  return { sendMessage }
}
