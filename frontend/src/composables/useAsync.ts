import { ref, shallowRef, type Ref, type ShallowRef } from 'vue';

import { getErrorMessage, isMissingResource } from '@/api/client';

export type AsyncState<TData> = {
  readonly data: ShallowRef<TData | undefined>;
  readonly error: Ref<string | undefined>;
  /** The load failed because the thing doesn't exist (for this user), so a retry is pointless. */
  readonly isMissing: Ref<boolean>;
  readonly isLoading: Ref<boolean>;
  readonly reload: () => Promise<void>;
};

export function useAsync<TData>(load: () => Promise<TData>): AsyncState<TData> {
  const data = shallowRef<TData>();
  const error = ref<string>();
  const isMissing = ref(false);
  const isLoading = ref(true);

  async function reload(): Promise<void> {
    isLoading.value = true;
    error.value = undefined;
    isMissing.value = false;
    try {
      data.value = await load();
    } catch (failure: unknown) {
      error.value = getErrorMessage(failure);
      isMissing.value = isMissingResource(failure);
    } finally {
      isLoading.value = false;
    }
  }

  void reload();
  return { data, error, isMissing, isLoading, reload };
}
