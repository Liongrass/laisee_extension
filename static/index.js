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
            name: 'title',
            label: 'Title',
            align: 'left',
            field: 'title'
          },
          {
            name: 'status',
            label: 'Status',
            align: 'left',
            format: (_, row) => this.stateLabel(row)
          },
          {
            name: 'amount',
            label: 'Amount (sat)',
            align: 'left',
            format: (_, row) => {
              if (row.is_paid) return String(row.paid_amount)
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
          max_sats: 1000
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
      if (row.is_withdrawn) return '⚫ Withdrawn'
      if (row.is_paid) return '🟢 Funded'
      return '🟠 Unfunded'
    },
    getLaisees() {
      LNbits.api
        .request(
          'GET',
          '/laisee/api/v1/laisees?all_wallets=true',
          this.g.user.wallets[0].inkey
        )
        .then(response => {
          this.laisees = response.data
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
          max_sats: this.formDialog.data.max_sats
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
          max_sats: 1000
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
