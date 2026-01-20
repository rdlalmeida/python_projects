/**
    This transaction finishes an Election by setting the provided dictionary as the final election results and by setting the isFinished flag to true.

    @param electionResults ({String: Int}) The dictionary of election results to set in this election, in the format {election_option: vote_count}
    @param ballotReceipts ([UInt64]) A list with all the ballot receipts extracted from the encrypted Ballot options.
    @param electionId (UInt64) The election identifier for the election to finish.
**/

import ElectionStandard from 0x287f5c8b0865c516
import VoteBooth from 0x287f5c8b0865c516

transaction(electionId: UInt64, electionResults: {String: Int}, ballotReceipts: [UInt64]) {
    let electionIndexRef: &VoteBooth.ElectionIndex
    let electionRef: auth(ElectionStandard.ElectionAdmin) &ElectionStandard.Election
    let deployerAddress: Address
    let signerAddress: Address

    prepare(signer: auth(Storage, ElectionStandard.ElectionAdmin, BorrowValue) &Account) {
        self.deployerAddress = VoteBooth.deployerAddress
        self.signerAddress = signer.address

        let deployerAccount: &Account = getAccount(self.deployerAddress)

        self.electionIndexRef = signer.storage.borrow<&VoteBooth.ElectionIndex>(from: VoteBooth.electionIndexStoragePath) ??
        panic(
            "Unable to retrieve a valid &VoteBooth.ElectionIndex at"
            .concat(VoteBooth.electionIndexStoragePath.toString())
            .concat(" from account ")
            .concat(signer.address.toString())
        )

        let electionStoragePath: StoragePath = self.electionIndexRef.getElectionStoragePath(electionId: electionId) ??
        panic(
            "Unable to get a valid StoragePath for Election "
            .concat(electionId.toString())
            .concat(" from the ElectionIndexPublic from account ")
            .concat(self.deployerAddress.toString())
        )

        self.electionRef = signer.storage.borrow<auth(ElectionStandard.ElectionAdmin) &ElectionStandard.Election>(from: electionStoragePath) ??
        panic(
            "Unable to retrieve a valid auth(ElectionStandard.ElectionAdmin) &ElectionStandard.Election at "
            .concat(electionStoragePath.toString())
            .concat(" from account ")
            .concat(self.deployerAddress.toString())
        )
    }

    execute {
        let result: Bool = self.electionRef.finishElection(electionResults: electionResults, ballotReceipts: ballotReceipts)

        // Finish by removing the Election from the ElectionIndex
        let removalResults: {StoragePath: PublicPath}? = self.electionIndexRef.removeElectionFromIndex(electionId: electionId)

        log(
            "Removed Election "
            .concat(electionId.toString())
            .concat(" from the ElectionIndex in account ")
            .concat(self.signerAddress.toString())
        )
    }
}