export interface KeyValueStore {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
  removeItem(key: string): Promise<void>;
}

export class MemoryKeyValueStore implements KeyValueStore {
  readonly values = new Map<string, string>();

  async getItem(key: string): Promise<string | null> {
    return this.values.get(key) ?? null;
  }

  async setItem(key: string, value: string): Promise<void> {
    this.values.set(key, value);
  }

  async removeItem(key: string): Promise<void> {
    this.values.delete(key);
  }
}

export class DreamDraftStore {
  static readonly DRAFT_KEY = 'apex.dream-builder.dream-intake.draft.v0.3.1';

  private readonly store: KeyValueStore;

  constructor(store: KeyValueStore) {
    this.store = store;
  }

  async saveDraft(dream: string): Promise<void> {
    await this.store.setItem(DreamDraftStore.DRAFT_KEY, dream);
  }

  async loadDraft(): Promise<string> {
    return (await this.store.getItem(DreamDraftStore.DRAFT_KEY)) ?? '';
  }

  async clearDraft(): Promise<void> {
    await this.store.removeItem(DreamDraftStore.DRAFT_KEY);
  }
}
