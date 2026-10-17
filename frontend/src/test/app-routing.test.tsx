import { QueryClient } from "@tanstack/react-query";
import { createMemoryHistory, createRouter, RouterProvider } from "@tanstack/react-router";
import { cleanup, render, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { routeTree } from "@/routeTree.gen";

async function renderAt(path: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const router = createRouter({
    routeTree,
    context: { queryClient },
    history: createMemoryHistory({ initialEntries: [path] }),
  });
  await router.load();
  return render(<RouterProvider router={router} />);
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("App routing", () => {
  it("renders the index route", async () => {
    await renderAt("/");

    await waitFor(() => {
      expect(document.body.innerHTML).toContain("TalkTribe");
    });
  });

  it("renders the not-found route", async () => {
    vi.spyOn(console, "warn").mockImplementation(() => undefined);
    vi.spyOn(console, "error").mockImplementation(() => undefined);

    await renderAt("/this-route-does-not-exist");

    await waitFor(() => {
      expect(document.body.innerHTML).toContain("404");
    });
  });

  it("renders the profile route without crashing", async () => {
    await renderAt("/profile");
    await waitFor(() => {
      expect(document.body.innerHTML).not.toContain("This page didn't load");
    });
  });

  it("renders the partner profile route without crashing", async () => {
    await renderAt("/partners/1");
    await waitFor(() => {
      expect(document.body.innerHTML).not.toContain("This page didn't load");
    });
  });
});
