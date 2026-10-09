function laiseeStateLabel(row) {
  if (row.is_withdrawn) return '⚫ Withdrawn'
  if (row.is_paid) return '🟢 Funded'
  return '🟠 Unfunded'
}

window.PageLaisee = {
  template: '#page-laisee',
  computed: {
    baseUrl() {
      return window.location.origin + '/laisee/api/v1/laisees'
    }
  },
  data() {
    return {
      activeUrl: '',
      laisees: [],
      laiseeTable: {
        columns: [
          {
            name: 'id',
            label: 'ID',
            align: 'left',
            field: 'id'
          },
          {
            name: 'title',
            label: 'Title',
            align: 'left',
            field: 'title'
          },
          {
            name: 'status',
            label: 'Status',
            align: 'left',
            format: (_, row) => laiseeStateLabel(row)
          },
          {
            name: 'amount',
            label: 'Amount (sat)',
            align: 'left',
            format: (_, row) => {
              if (row.is_paid) return String(row.withdrawable_sats ?? row.paid_amount)
              if (row.min_sats === row.max_sats) return String(row.min_sats)
              return `${row.min_sats} – ${row.max_sats}`
            }
          },
          {
            name: 'created_at',
            label: 'Created',
            align: 'left',
            field: 'created_at',
            format: val => (val ? LNbits.utils.formatDate(val) : '—')
          }
        ],
        pagination: {rowsPerPage: 10}
      },
      formDialog: {
        show: false,
        data: {
          min_sats: 1000,
          max_sats: 1000,
          allow_comment: false,
          deduct_fees: false
        }
      },
      qrCodeDialog: {
        show: false,
        data: null
      }
    }
  },
  methods: {
    stateLabel(row) {
      return laiseeStateLabel(row)
    },
    getLaisees() {
      // The claim link (lnurl_url) is only returned to admin-key callers,
      // so fetch each wallet's laisees with that wallet's own admin key.
      Promise.all(
        this.g.user.wallets.map(wallet =>
          LNbits.api.request('GET', '/laisee/api/v1/laisees', wallet.adminkey)
        )
      )
        .then(responses => {
          this.laisees = responses
            .flatMap(response => response.data)
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        })
        .catch(LNbits.utils.notifyApiError)
    },
    openQrCodeDialog(laiseeId) {
      const laisee = this.laisees.find(l => l.id === laiseeId)
      if (!laisee) return
      this.activeUrl = laisee.lnurl_url
      this.qrCodeDialog.data = laisee
      this.qrCodeDialog.show = true
    },
    createLaisee() {
      const wallet = this.g.user.wallets.find(
        w => w.id === this.formDialog.data.wallet
      )
      if (!wallet) return

      LNbits.api
        .request('POST', '/laisee/api/v1/laisees', wallet.adminkey, {
          title: this.formDialog.data.title,
          wallet: wallet.id,
          min_sats: this.formDialog.data.min_sats,
          max_sats: this.formDialog.data.max_sats,
          allow_comment: this.formDialog.data.allow_comment,
          deduct_fees: this.formDialog.data.deduct_fees
        })
        .then(response => {
          this.laisees.unshift(response.data)
          this.formDialog.show = false
          this.resetFormData()
        })
        .catch(LNbits.utils.notifyApiError)
    },
    deleteLaisee(laiseeId) {
      const laisee = this.laisees.find(l => l.id === laiseeId)
      if (!laisee) return

      LNbits.utils
        .confirmDialog('Are you sure you want to delete this laisee?')
        .onOk(() => {
          const wallet = this.g.user.wallets.find(w => w.id === laisee.wallet)
          if (!wallet) return

          LNbits.api
            .request(
              'DELETE',
              `/laisee/api/v1/laisees/${laiseeId}`,
              wallet.adminkey
            )
            .then(() => {
              this.laisees = this.laisees.filter(l => l.id !== laiseeId)
            })
            .catch(LNbits.utils.notifyApiError)
        })
    },
    resetFormData() {
      this.formDialog = {
        show: false,
        data: {
          min_sats: 1000,
          max_sats: 1000,
          allow_comment: false,
          deduct_fees: false
        }
      }
    }
  },
  created() {
    if (this.g.user.wallets?.length) {
      this.getLaisees()
    }
  }
}
