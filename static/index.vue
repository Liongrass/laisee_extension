<template id="page-laisee">
  <div class="row q-col-gutter-md">
    <!-- ── Left column: table + create button ── -->
    <div class="col-12 col-md-7 q-gutter-y-md">
      <q-card>
        <q-card-section>
          <q-btn unelevated color="primary" @click="formDialog.show = true">
            New Laisee
          </q-btn>
        </q-card-section>
      </q-card>

      <q-card>
        <q-card-section>
          <div class="row items-center no-wrap q-mb-md">
            <div class="col">
              <h5 class="text-subtitle1 q-my-none">Laisees</h5>
            </div>
          </div>
          <q-table
            dense
            flat
            :rows="laisees"
            :columns="laiseeTable.columns"
            row-key="id"
            v-model:pagination="laiseeTable.pagination"
          >
            <template v-slot:header="props">
              <q-tr class="text-left" :props="props">
                <q-th auto-width></q-th>
                <q-th v-for="col in props.cols" :key="col.name" :props="props">
                  <span v-text="col.label"></span>
                </q-th>
              </q-tr>
            </template>
            <template v-slot:body="props">
              <q-tr :props="props">
                <q-td auto-width>
                  <q-btn
                    dense
                    size="xs"
                    icon="visibility"
                    :color="$q.dark.isActive ? 'grey-7' : 'grey-5'"
                    class="q-ml-sm"
                    @click="openQrCodeDialog(props.row.id)"
                  >
                    <q-tooltip>View QR / LNURL</q-tooltip>
                  </q-btn>
                  <q-btn
                    flat
                    dense
                    size="xs"
                    icon="cancel"
                    color="pink"
                    class="q-ml-sm"
                    @click="deleteLaisee(props.row.id)"
                  >
                    <q-tooltip>Delete</q-tooltip>
                  </q-btn>
                </q-td>
                <q-td
                  v-for="col in props.cols"
                  :key="col.name"
                  :props="props"
                  v-text="col.value"
                ></q-td>
              </q-tr>
            </template>
          </q-table>
        </q-card-section>
      </q-card>
    </div>

    <!-- ── Right column: about + API docs ── -->
    <div class="col-12 col-md-5 q-gutter-y-md">
      <q-card>
        <q-card-section>
          <h6 class="text-subtitle1 q-my-none">Laisee extension</h6>
        </q-card-section>
        <q-card-section class="q-pa-none">
          <q-separator></q-separator>
          <q-list>
            <q-expansion-item
              group="extras"
              icon="swap_vertical_circle"
              label="API info"
              :content-inset-level="0.5"
            >
              <q-btn
                flat
                label="Swagger API"
                type="a"
                href="../docs#/laisee"
              ></q-btn>
              <q-expansion-item
                group="api"
                dense
                expand-separator
                label="List laisees"
              >
                <q-card>
                  <q-card-section>
                    <code
                      ><span class="text-blue">GET</span>
                      /laisee/api/v1/laisees</code
                    >
                    <h5 class="text-caption q-mt-sm q-mb-none">Headers</h5>
                    <code>{"X-Api-Key": &lt;invoice_key&gt;}</code>
                    <h5 class="text-caption q-mt-sm q-mb-none">Returns 200 OK</h5>
                    <code>[&lt;laisee_object&gt;, ...]</code>
                    <h5 class="text-caption q-mt-sm q-mb-none">Curl example</h5>
                    <code
                      >curl -X GET
                      <span v-text="baseUrl"></span>
                      -H "X-Api-Key:
                      <span v-text="g.user.wallets[0].inkey"></span>"
                    </code>
                  </q-card-section>
                </q-card>
              </q-expansion-item>
              <q-expansion-item
                group="api"
                dense
                expand-separator
                label="Create a laisee"
              >
                <q-card>
                  <q-card-section>
                    <code
                      ><span class="text-green">POST</span>
                      /laisee/api/v1/laisees</code
                    >
                    <h5 class="text-caption q-mt-sm q-mb-none">Headers</h5>
                    <code>{"X-Api-Key": &lt;admin_key&gt;}</code>
                    <h5 class="text-caption q-mt-sm q-mb-none">
                      Body (application/json)
                    </h5>
                    <code
                      >{"title": &lt;string&gt;, "min_sats": &lt;integer&gt;,
                      "max_sats": &lt;integer&gt;}</code
                    >
                    <h5 class="text-caption q-mt-sm q-mb-none">
                      Returns 201 CREATED
                    </h5>
                    <code>{"id": ..., "lnurl_url": ..., ...}</code>
                    <h5 class="text-caption q-mt-sm q-mb-none">Curl example</h5>
                    <code
                      >curl -X POST
                      <span v-text="baseUrl"></span>
                      -d '{"title":"Happy New Year","min_sats":1000,"max_sats":1000}'
                      -H "Content-type: application/json"
                      -H "X-Api-Key:
                      <span v-text="g.user.wallets[0].adminkey"></span>"
                    </code>
                  </q-card-section>
                </q-card>
              </q-expansion-item>
              <q-expansion-item
                group="api"
                dense
                expand-separator
                label="Delete a laisee"
                class="q-pb-md"
              >
                <q-card>
                  <q-card-section>
                    <code
                      ><span class="text-pink">DELETE</span>
                      /laisee/api/v1/laisees/&lt;laisee_id&gt;</code
                    >
                    <h5 class="text-caption q-mt-sm q-mb-none">Headers</h5>
                    <code>{"X-Api-Key": &lt;admin_key&gt;}</code>
                    <h5 class="text-caption q-mt-sm q-mb-none">
                      Returns 200 OK
                    </h5>
                    <h5 class="text-caption q-mt-sm q-mb-none">Curl example</h5>
                    <code
                      >curl -X DELETE
                      <span
                        v-text="baseUrl + '/&lt;laisee_id&gt;'"
                      ></span>
                      -H "X-Api-Key:
                      <span v-text="g.user.wallets[0].adminkey"></span>"
                    </code>
                  </q-card-section>
                </q-card>
              </q-expansion-item>
            </q-expansion-item>
            <q-separator></q-separator>
            <q-expansion-item
              group="extras"
              icon="info"
              label="About Laisee"
            >
              <q-card>
                <q-card-section>
                  <p>
                    A <strong>laisee</strong> is a digital red envelope.<br /><br />
                    Create one and share the QR code. The first person to scan
                    it sees an <strong>LNURL-pay</strong> and funds the envelope.
                    Once funded, the same QR code becomes an
                    <strong>LNURL-withdraw</strong> — anyone who scans it can
                    redeem the sats inside.
                  </p>
                  <p>
                    <strong>States:</strong><br />
                    🟠 <em>Unfunded</em> — waiting for first payment<br />
                    🟢 <em>Funded</em> — ready to withdraw<br />
                    ⚫ <em>Withdrawn</em> — spent
                  </p>
                </q-card-section>
              </q-card>
            </q-expansion-item>
          </q-list>
        </q-card-section>
      </q-card>
    </div>

    <!-- ── Create dialog ── -->
    <q-dialog v-model="formDialog.show" @hide="resetFormData">
      <q-card class="q-pa-lg q-pt-xl lnbits__dialog-card">
        <q-form @submit="createLaisee" class="q-gutter-md">
          <q-select
            filled
            dense
            emit-value
            v-model="formDialog.data.wallet"
            :options="g.user.walletOptions"
            label="Wallet *"
          ></q-select>
          <q-input
            filled
            dense
            v-model.trim="formDialog.data.title"
            type="text"
            label="Title / description *"
          ></q-input>
          <div class="row q-col-gutter-sm">
            <div class="col-6">
              <q-input
                filled
                dense
                v-model.number="formDialog.data.min_sats"
                type="number"
                min="1"
                label="Min amount (sat) *"
              ></q-input>
            </div>
            <div class="col-6">
              <q-input
                filled
                dense
                v-model.number="formDialog.data.max_sats"
                type="number"
                min="1"
                label="Max amount (sat) *"
              ></q-input>
            </div>
          </div>
          <div class="row q-mt-lg">
            <q-btn
              unelevated
              color="primary"
              type="submit"
              :disable="
                !formDialog.data.wallet ||
                !formDialog.data.title ||
                !(formDialog.data.min_sats > 0) ||
                !(formDialog.data.max_sats > 0)
              "
            >
              Create Laisee
            </q-btn>
            <q-btn v-close-popup flat color="grey" class="q-ml-auto">
              Cancel
            </q-btn>
          </div>
        </q-form>
      </q-card>
    </q-dialog>

    <!-- ── QR code dialog ── -->
    <q-dialog v-model="qrCodeDialog.show" position="top">
      <q-card v-if="qrCodeDialog.data" class="q-pa-lg lnbits__dialog-card">
        <lnbits-qrcode-lnurl
          :url="activeUrl"
          :nfc="true"
        ></lnbits-qrcode-lnurl>
        <p style="word-break: break-all" class="q-mt-md">
          <strong>ID:</strong>
          <span v-text="qrCodeDialog.data.id"></span><br />
          <strong>Title:</strong>
          <span v-text="qrCodeDialog.data.title"></span><br />
          <strong>Status:</strong>
          <span v-text="stateLabel(qrCodeDialog.data)"></span><br />
          <span v-if="!qrCodeDialog.data.is_paid">
            <strong>Pay range:</strong>
            <span
              v-text="qrCodeDialog.data.min_sats + ' – ' + qrCodeDialog.data.max_sats + ' sat'"
            ></span>
          </span>
          <span v-else>
            <strong>Withdraw amount:</strong>
            <span v-text="qrCodeDialog.data.paid_amount + ' sat'"></span>
          </span>
        </p>
        <div class="row q-mt-lg q-gutter-sm">
          <q-btn
            outline
            color="grey"
            @click="utils.copyText(activeUrl, 'URL copied to clipboard!')"
          >
            Copy URL
          </q-btn>
          <q-btn v-close-popup flat color="grey" class="q-ml-auto">
            Close
          </q-btn>
        </div>
      </q-card>
    </q-dialog>
  </div>
</template>
