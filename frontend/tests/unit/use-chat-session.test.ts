import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useChatSession } from "@/components/chat/useChatSession";

// Feature 002 (FR-017): envio do conversation_id em POST /api/chat.

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function doneResponse(): Response {
  const body = 'event: done\ndata: {"outcome":"answered","suggestions":[]}\n\n';
  return new Response(body, { status: 200, headers: { "Content-Type": "text/event-stream" } });
}

const fetchMock = vi.fn();

function sentBodies(): Record<string, unknown>[] {
  return fetchMock.mock.calls.map(([, init]) => JSON.parse((init as RequestInit).body as string));
}

async function sendTwice() {
  const { result } = renderHook(() => useChatSession("pt-BR"));
  await act(() => result.current.send("primeira"));
  await act(() => result.current.send("segunda"));
}

describe("useChatSession: conversation_id", () => {
  beforeEach(() => {
    fetchMock.mockReset();
    fetchMock.mockImplementation(async () => doneResponse());
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    localStorage.clear();
    sessionStorage.clear();
  });

  it("envia o mesmo UUID em todas as perguntas da conversa", async () => {
    await sendTwice();

    const [first, second] = sentBodies();
    expect(first.conversation_id).toMatch(UUID_PATTERN);
    expect(second.conversation_id).toBe(first.conversation_id);
  });

  it("gera outro valor numa nova montagem do hook", async () => {
    await sendTwice();
    await sendTwice();

    const bodies = sentBodies();
    expect(bodies[2].conversation_id).not.toBe(bodies[0].conversation_id);
  });

  it("funciona sem crypto.randomUUID, omitindo o campo", async () => {
    vi.stubGlobal("crypto", {});

    await sendTwice();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    for (const body of sentBodies()) {
      expect(body).not.toHaveProperty("conversation_id");
    }
  });

  it("não grava nada no armazenamento do navegador", async () => {
    await sendTwice();

    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });
});
